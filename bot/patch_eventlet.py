import eventlet

# Патчим стандартные библиотеки до импорта любых других модулей
eventlet.monkey_patch()
