## Запуск

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py                          # GUI: Original | DCT | DWT
.venv/bin/python main.py path/to/image.png        # інше зображення
.venv/bin/python experiments.py --out results     # таблиця PSNR + графіки
.venv/bin/python experiments.py --percents 10 5 1 --levels 3
```
