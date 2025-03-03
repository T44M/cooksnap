import os
import json
import logging
import base64
import boto3
import requests
from io import BytesIO
from datetime import datetime

# ロガー設定
logger = logging.getLogger()

# Claude API設定
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

def generate_recipe_from_image(image_data, user_id):
    """
    食材画像からレシピを生成する
    """
    try:
        # 画像をBase64エンコード
        image_data.seek(0)
        image_base64 = base64.b64encode(image_data.read()).decode('utf-8')
        
        # Claudeへのプロンプト
        prompt = """
        あなたは料理のエキスパートです。この画像に写っている食材を詳細に特定し、それらを使った簡単なレシピを考えてください。
        
        # 回答形式
        ## 特定できた食材
        - [食材1]
        - [食材2]
        ...
        
        ## おすすめレシピ
        **[レシピ名]**
        
        **材料（2人前）**
        - [特定された食材] [量]
        - [追加材料1] [量]
        ...
        
        **作り方**
        1. [手順1]
        2. [手順2]
        ...
        
        **調理時間**: 約[X]分
        
        ## ポイント
        [調理のコツや栄養情報など簡潔に]
        
        # 注意事項
        - 一般家庭で作りやすい簡単なレシピにしてください
        - 特別な調理器具を必要としないレシピを優先してください
        - 調理手順は5ステップ程度にまとめてください
        - 日本の一般家庭で手に入りやすい材料を使ってください
        """
        
        # Claude APIリクエスト
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(
            CLAUDE_API_URL,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"Claude API error: {response.text}")
            return "レシピの生成中にエラーが発生しました。申し訳ありませんが、もう一度お試しください。"
            
        result = response.json()
        recipe_text = result["content"][0]["text"]
        
        # DynamoDBにレシピを保存（後で実装）
        
        return recipe_text
        
    except Exception as e:
        logger.error(f"Error generating recipe: {e}")
        return "レシピの生成中にエラーが発生しました。申し訳ありませんが、もう一度お試しください。"