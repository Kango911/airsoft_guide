#!/usr/bin/env python3
"""
Проверка VK токена
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))


def check_vk_token():
    """Проверка работоспособности VK токена"""
    try:
        from key.key import VK_ACCESS_TOKEN

        if not VK_ACCESS_TOKEN or VK_ACCESS_TOKEN.startswith('ВАШ_'):
            print("❌ VK токен не настроен в key/key.py")
            print("📝 Получите токен здесь: https://vk.com/dev/access_token")
            return False

        # Простая проверка формата токена
        if VK_ACCESS_TOKEN.startswith('vk1.a.'):
            print("✅ Формат токена: пользовательский токен")
        else:
            print("⚠️ Нестандартный формат токена")

        # Пробуем сделать тестовый запрос
        import requests

        url = "https://api.vk.com/method/users.get"
        params = {
            'access_token': VK_ACCESS_TOKEN,
            'v': '5.131'
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if 'error' in data:
            error = data['error']
            print(f"❌ Ошибка VK API: {error.get('error_msg')}")
            print(f"🔧 Код ошибки: {error.get('error_code')}")

            if error.get('error_code') == 5:
                print("💡 Токен невалиден или устарел")
            elif error.get('error_code') == 6:
                print("💡 Слишком много запросов, попробуйте позже")
            elif error.get('error_code') == 15:
                print("💡 Нет доступа к группе")

            return False
        else:
            print("✅ VK токен работает корректно!")
            user_info = data['response'][0]
            print(f"👤 Пользователь: {user_info.get('first_name')} {user_info.get('last_name')}")
            return True

    except ImportError:
        print("❌ Не удалось импортировать VK_ACCESS_TOKEN из key/key.py")
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Проверка VK токена...")
    check_vk_token()