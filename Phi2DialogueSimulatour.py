"""
Phi-2専用：軽量LLM対話シミュレーション
メモリ効率とPhi-2の特性に最適化
"""

import torch
import csv
import random
import os
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Error: pip install transformers torch")


class Phi2DialogueSimulator:
    """Phi-2専用の最適化シミュレーター"""
    
    def __init__(self, use_gpu=True):
        """
        Phi-2専用初期化
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers required")
        
        self.model_name = "microsoft/phi-2"
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        
        print(f"Loading Phi-2 on {self.device}...")
        
        # Phi-2のロード
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map=self.device,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        # パディングトークン設定
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        print("✓ Model loaded successfully")

        # CSVデータ読み込み
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.jobs = self._load_csv(os.path.join(base_dir, "data", "jobs.csv"))
        self.personalities = self._load_csv(os.path.join(base_dir, "data", "personatlities.csv"))
        self.names = self._load_names(os.path.join(base_dir, "data", "names.csv"))
        print(f"✓ Loaded {len(self.jobs)} jobs, {len(self.personalities)} personalities, {len(self.names)} names")

        # 対話履歴
        self.conversation_history = []
    
    @staticmethod
    def _load_csv(path: str) -> List[Dict]:
        """CSVファイルを辞書リストとして読み込む"""
        with open(path, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    @staticmethod
    def _load_names(path: str) -> List[str]:
        """名前ファイルを読み込む（1行1名前）"""
        with open(path, encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def create_random_character(self) -> Dict:
        """ランダムにジョブと性格を選んでキャラクターを生成"""
        job = random.choice(self.jobs)
        personality = random.choice(self.personalities)
        name = random.choice(self.names)

        character = {
            'name': name,
            'job': job['Class'],
            'role': job['Role'],
            'weapon': job['Primary_Weapon'],
            'primary_stat': job['Primary_Stat'],
            'description': job['Description'],
            'abilities': job['Typical_Abilities'],
            'personality': personality['Trait'],
            'personality_desc': personality['Description'],
            'hp': int(personality['HP']),
            'atk': int(personality['ATK']),
            'def': int(personality['DEF']),
            'wis': int(personality['WIS']),
            'luc': int(personality['LUC']),
            'agi': int(personality['AGI']),
        }

        print(f"\n--- キャラクター生成 ---")
        print(f"名前: {name}")
        print(f"職業: {job['Class']} ({job['Role']}) - {job['Description']}")
        print(f"性格: {personality['Trait']} - {personality['Description']}")
        print(f"武器: {job['Primary_Weapon']} / 能力: {job['Typical_Abilities']}")
        stat_mods = [f"HP{character['hp']:+d}", f"ATK{character['atk']:+d}",
                     f"DEF{character['def']:+d}", f"WIS{character['wis']:+d}",
                     f"LUC{character['luc']:+d}", f"AGI{character['agi']:+d}"]
        print(f"性格補正: {', '.join(stat_mods)}")
        print(f"-----------------------")

        return character

    def generate_response(self,
                        user_input: str,
                        character: Dict,
                        is_first_greeting: bool = False) -> str:
        name = character['name']
        role = character['role']

        if is_first_greeting:
            # 初回専用のシンプルなプロンプト
            prompt = f"""A traveler meets {name}, a {character['personality']} {character['job']}.

    {name}'s profile:
    - Role: {role}
    - Weapon: {character['weapon']}
    - Skills: {character['abilities']}
    - Personality: {character['personality']}

    Traveler: {user_input}
    {name}: I am"""
            
            max_tokens = 80
            temp = 0.5
        else:
            # 既存の会話継続用プロンプト
            system_msg = f"I am {name}, a {character['personality']} {character['job']}."
            
            conversation_context = ""
            if self.conversation_history:
                recent_turns = self.conversation_history[-3:]
                lines = []
                for t in recent_turns:
                    lines.append(f"User: {t['user']}")
                    lines.append(f"{name}: {t['ai']}")
                conversation_context = "\n" + "\n".join(lines) + "\n"

            prompt = f"""{system_msg}

    {conversation_context}User: {user_input}
    {name}:"""
            
            max_tokens = 50
            temp = 0.7
        
        inputs = self.tokenizer(
            prompt, 
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temp,
                top_p=0.85,
                top_k=30,
                repetition_penalty=1.3,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = self._extract_phi2_response(full_response, prompt, name)
        
        return response
    
    def _extract_phi2_response(self, full_text: str, prompt: str, char_name: str) -> str:
        """Phi-2の出力から応答を抽出"""
        
        # プロンプトを削除
        if prompt in full_text:
            response = full_text[len(prompt):].strip()
        else:
            response = full_text.strip()
        
        # 最初の文または改行まで
        if '\n' in response:
            response = response.split('\n')[0]
        
        # キャラクター名を削除（重複している場合）
        if response.startswith(f"{char_name}:"):
            response = response[len(f"{char_name}:"):].strip()
        
        # 最初の1-2文のみ
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if sentences:
            response = '. '.join(sentences[:2]) + '.'
        
        # 長すぎる場合は切る（Phi-2は暴走しやすい）
        if len(response) > 200:
            response = response[:200].rsplit(' ', 1)[0] + '...'
        
        return response.strip()
    
    def simulate_conversation(self,
                             scenario: List[str],
                             character: Dict) -> Tuple[bool, float, Dict]:
        """
        会話シミュレーション

        Args:
            scenario: ユーザー発言リスト
            character: create_random_character() で生成したキャラクター辞書
        """
        name = character['name']

        print("\n" + "="*60)
        print(f"シミュレーション: {name} ({character['job']} / {character['personality']})")
        print("="*60)

        for turn_idx, user_input in enumerate(scenario, 1):
            print(f"\n[ターン {turn_idx}]")
            print(f"User: {user_input}")

            # AI応答生成
            ai_response = self.generate_response(user_input, character)
            print(f"{name}: {ai_response}")

            # 記録
            self.conversation_history.append({
                'turn': turn_idx,
                'user': user_input,
                'ai': ai_response
            })

        # 最終判定：transformerによる二値分類
        return self._classify_companion(character)

    def _classify_companion(self, character: Dict) -> Tuple[bool, float, Dict]:
        """
        会話履歴全体をtransformerに入力し、仲間になるかを二値分類する。
        YESトークンとNOトークンの生成確率を比較して判定。
        """

        if not self.conversation_history:
            return False, 0.0, {}

        name = character['name']
        job = character['job']
        personality = character['personality']

        # 会話履歴をテキストに整形
        dialogue_lines = []
        for turn in self.conversation_history:
            dialogue_lines.append(f"User: {turn['user']}")
            dialogue_lines.append(f"{name}: {turn['ai']}")
        dialogue_text = "\n".join(dialogue_lines)

        # 分類プロンプト
        prompt = f"""Instruct: Read the following conversation between a user and {name} (a {personality} {job}).
Based on the conversation, does {name} want to join the user's party as a companion?

Conversation:
{dialogue_text}

Answer YES if {name} is willing to join. Answer NO if {name} is unwilling or the role is incompatible.
Output:"""

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)

        # 次トークンのロジットを取得（生成はしない）
        with torch.no_grad():
            outputs = self.model(**inputs)
            next_token_logits = outputs.logits[:, -1, :]

        # YES / NO それぞれのトークンIDを取得
        yes_tokens = self.tokenizer.encode(" YES", add_special_tokens=False)
        no_tokens = self.tokenizer.encode(" NO", add_special_tokens=False)

        # 各トークン列の先頭トークンのロジットで比較
        yes_logit = next_token_logits[0, yes_tokens[0]].item()
        no_logit = next_token_logits[0, no_tokens[0]].item()

        # softmaxで確率化
        logits_pair = torch.tensor([yes_logit, no_logit])
        probs = torch.softmax(logits_pair, dim=0)
        yes_prob = probs[0].item()
        no_prob = probs[1].item()

        # 確率的判定
        random_value = random.random()  # 0.0～1.0の乱数生成

        if yes_prob >= 0.8:
            # 80%以上なら確定でYES
            becomes_companion = True
            decision_type = "確定YES (≥80%)"
        elif yes_prob <= 0.20:
            # 10%以下なら確定でNO
            becomes_companion = False
            decision_type = "確定NO (≤20%)"
        else:
            # 10%～90%の間は確率的判定
            becomes_companion = random_value < yes_prob
            decision_type = f"確率的判定 (乱数={random_value:.3f})"

        confidence = max(yes_prob, no_prob)

        details = {
            'yes_prob': yes_prob,
            'no_prob': no_prob,
            'confidence': confidence,
            'yes_logit': yes_logit,
            'no_logit': no_logit,
            'random_value': random_value,
            'decision_type': decision_type
        }

        # 結果表示
        print("\n" + "="*60)
        print("最終判定（確率的二値分類）")
        print("="*60)
        print(f"仲間になる: {'✓ YES' if becomes_companion else '✗ NO'}")
        print(f"YES確率: {yes_prob:.3f}")
        print(f"NO確率:  {no_prob:.3f}")
        print(f"乱数値:  {random_value:.3f}")
        print(f"判定方式: {decision_type}")
        print(f"確信度:  {confidence:.3f}")
        print("="*60)

        return becomes_companion, yes_prob, details
    
    def reset(self):
        """履歴リセット"""
        self.conversation_history = []