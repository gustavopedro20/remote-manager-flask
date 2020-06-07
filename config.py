import os

mail_settings = {
    'MAIL_SERVER': 'smtp.gmail.com',
    'MAIL_PORT': 465,
    'MAIL_USE_TLS': False,
    'MAIL_USE_SSL': True,
    'MAIL_USERNAME': os.getenv('MAIL_USERNAME', 'email@localhost'),
    'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD', 'password')
}

sql_setting = {
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///remote_manager.db'
}
