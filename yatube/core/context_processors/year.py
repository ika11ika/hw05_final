from datetime import date


def year(request):
    """Вычисление текущего года в переменную """
    return {"year": date.today().year}
