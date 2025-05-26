# bot/patch_eventlet.py
import eventlet

# Патчим стандартные библиотеки ДО импорта любых других модулей,
# особенно тех, которые используют сокеты или ввод-вывод.
# Это должно быть первым, что импортируется в Celery worker.
eventlet.monkey_patch()
print("Eventlet monkey patching applied.")
