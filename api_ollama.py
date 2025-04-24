import io

from ollama import Client
from PIL import Image
def img_to_txt(img_path, token_limit):

    client = Client(
        host="http://192.168.2.250:11434",
    )
    image = Image.open(img_path)
    img_byte = io.BytesIO()
    image.save(img_byte, format="JPEG")
    img_byte = img_byte.getvalue()
    response = client.chat(
        model="gemma3:12b",
        messages=[
            {
                'role': 'system',
                'content': f'请使用中文回复,回答的token不能超过{token_limit}',
            },
            {
                'role': 'user',
                "images": [img_byte]
            },
            {
                'role': 'user',
                'content': '请解释这张图片',
            }

        ]
    )
    # print(response, "1111111111111111111111111111111111")
    # print(response.message.content)
    return response.message.content