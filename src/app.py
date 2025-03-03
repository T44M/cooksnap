import json
import os
import base64
import hashlib
import hmac
import logging
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, TextSendMessage
)
import utils
import recipe

# ロガー設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数から設定を読み込み
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

# LINE Bot SDKのセットアップ
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def lambda_handler(event, context):
    """
    LINE Webhookを処理するメイン関数
    """
    logger.info('Event: %s', event)
    
    # リクエストボディの取得
    if 'body' not in event:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid request'})
        }
    
    body = event['body']
    signature = event['headers'].get('x-line-signature', '')
    
    # 署名検証
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error('Invalid signature')
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid signature'})
        }
    except Exception as e:
        logger.error('Error: %s', e)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'OK'})
    }

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """
    テキストメッセージの処理
    """
    text = event.message.text
    user_id = event.source.user_id
    
    # ユーザーが送ったテキストに応じた処理
    if text == "使い方":
        response_message = "食材の写真を送るだけで、AIがレシピを提案します。\n冷蔵庫の食材や買った野菜の写真を送ってみてください！"
    else:
        response_message = "食材の写真を送ってレシピを提案してもらいましょう！"
    
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_message)
        )
    except LineBotApiError as e:
        logger.error('LINE API Error: %s', e)

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    """
    画像メッセージの処理
    """
    user_id = event.source.user_id
    message_id = event.message.id
    
    try:
        # LINEから画像を取得
        image_content = utils.get_line_image(line_bot_api, message_id)
        
        # S3に画像をアップロード
        s3_url = utils.upload_to_s3(image_content, user_id, S3_BUCKET_NAME)
        
        # 処理中メッセージを送信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="食材を分析中です...しばらくお待ちください。")
        )
        
        # 非同期でレシピ生成処理を実行（この実装例では簡易化のため同期処理）
        # 実際には別のLambda関数に処理を委譲するなどの方法がよい
        generated_recipe = recipe.generate_recipe_from_image(image_content, user_id)
        
        # 分析結果・レシピをユーザーに送信
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=generated_recipe)
        )
        
    except Exception as e:
        logger.error('Error processing image: %s', e)
        # エラーメッセージを送信
        try:
            line_bot_api.push_message(
                user_id,
                TextSendMessage(text="申し訳ありません、画像の処理中にエラーが発生しました。もう一度お試しください。")
            )
        except LineBotApiError as line_error:
            logger.error('LINE API Error: %s', line_error)