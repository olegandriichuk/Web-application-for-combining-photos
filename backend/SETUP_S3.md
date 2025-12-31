# Налаштування Amazon S3 для зберігання фотографій

## Крок 1: Створення AWS акаунту
1. Перейдіть на https://aws.amazon.com/ та зареєструйтесь
2. Увійдіть в AWS Console

## Крок 2: Створення S3 Bucket
1. Відкрийте AWS Console
2. Знайдіть сервіс "S3" у пошуку
3. Натисніть "Create bucket"
4. Введіть унікальне ім'я для bucket (наприклад, `your-app-photos-bucket`)
5. Виберіть регіон (наприклад, `us-east-1`)
6. Налаштування блокування публічного доступу:
   - Якщо хочете публічний доступ до фото: зніміть всі галочки
   - Якщо хочете приватний доступ: залиште галочки (використовуватимуться presigned URLs)
7. Натисніть "Create bucket"

## Крок 3: Створення IAM користувача для програмного доступу
1. У AWS Console знайдіть сервіс "IAM"
2. Перейдіть до "Users" → "Create user"
3. Введіть ім'я користувача (наприклад, `photo-app-user`)
4. Виберіть "Access key - Programmatic access"
5. Натисніть "Next"
6. Виберіть "Attach policies directly"
7. Знайдіть та виберіть політику `AmazonS3FullAccess` (або створіть власну з обмеженими правами)
8. Натисніть "Create user"
9. **ВАЖЛИВО**: Збережіть `Access Key ID` та `Secret Access Key` - вони потрібні для налаштування

## Крок 4: Налаштування додатку
1. Створіть файл `.env` у директорії `backend/`:
```bash
cp .env.example .env
```

2. Відредагуйте файл `.env` та вставте ваші AWS credentials:
```env
AWS_ACCESS_KEY_ID=your_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name-here
```

## Крок 5: Встановлення залежностей
```bash
cd backend
pip install -r requirements.txt
```

## Крок 6: Оновлення бази даних
Оскільки модель `Photo` була змінена (поле `stored_name` замінено на `s3_key`), вам потрібно:

### Варіант A: Видалити стару базу даних (якщо немає важливих даних)
```bash
rm database.db  # або інше ім'я вашої бази даних
```
Таблиці будуть створені автоматично при запуску сервера.

### Варіант B: Використати міграції Alembic (якщо є важливі дані)
```bash
# Ініціалізація Alembic (якщо ще не зроблено)
alembic init alembic

# Створення міграції
alembic revision --autogenerate -m "Replace stored_name with s3_key"

# Застосування міграції
alembic upgrade head
```

## Крок 7: Запуск додатку
```bash
cd backend
uvicorn app.main:app --reload
```

## Додатково: CORS для S3 (якщо потрібен прямий доступ з браузера)
Якщо ви хочете, щоб фронтенд міг завантажувати файли безпосередньо в S3:

1. Відкрийте ваш S3 bucket
2. Перейдіть до "Permissions" → "CORS"
3. Додайте наступну конфігурацію:
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "ExposeHeaders": []
    }
]
```

## Тестування
1. Запустіть сервер
2. Відкрийте http://localhost:8000/docs
3. Спробуйте завантажити фото через endpoint `/photos`
4. Перевірте ваш S3 bucket - фото повинні з'явитися в папці `photos/`

## Альтернатива: Локальне тестування з LocalStack
Якщо хочете тестувати без AWS:

1. Встановіть LocalStack:
```bash
pip install localstack
```

2. Запустіть LocalStack:
```bash
localstack start
```

3. У файлі `.env` додайте:
```env
AWS_ENDPOINT_URL=http://localhost:4566
```

4. Створіть bucket у LocalStack:
```bash
aws --endpoint-url=http://localhost:4566 s3 mb s3://your-bucket-name
```

## Вартість
- S3 Storage: ~$0.023 за GB на місяць
- Запити GET: $0.0004 за 1000 запитів
- Запити PUT: $0.005 за 1000 запитів
- Безкоштовний рівень (Free Tier) для нових акаунтів: 5GB сховища, 20000 GET запитів, 2000 PUT запитів на місяць (протягом 12 місяців)
