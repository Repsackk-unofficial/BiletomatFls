from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'twoj_tajny_klucz_sesji'

def wczytaj_cennik():
    katalog_bazowy = os.path.dirname(os.path.abspath(__file__))
    sciezka = os.path.join(katalog_bazowy, 'cennik.json')
    try:
        with open(sciezka, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"BŁĄD: Nie znaleziono pliku pod ścieżką: {sciezka}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    cennik = wczytaj_cennik()
    if not cennik:
        return "Błąd: Brak pliku cennik.json w katalogu aplikacji!"

    if 'koszyk' not in session:
        session['koszyk'] = []
    if 'sciezka' not in session:
        session['sciezka'] = []

    if request.method == 'POST':
        akcja = request.form.get('akcja')
        klucz = request.form.get('klucz')

        if akcja == 'reset':
            session['sciezka'] = []
        elif akcja == 'wybierz' and klucz:
            poziom = cennik
            for k in session['sciezka']:
                poziom = poziom[k]

            if isinstance(poziom[klucz], dict):
                nowa_sciezka = list(session['sciezka'])
                nowa_sciezka.append(klucz)
                session['sciezka'] = nowa_sciezka
            else:
                pelna_nazwa = f"{' / '.join(session['sciezka'])} / {klucz}" if session['sciezka'] else klucz
                cena = poziom[klucz]

                koszyk = list(session['koszyk'])
                koszyk.append({"nazwa": pelna_nazwa, "cena": cena})
                session['koszyk'] = koszyk
                session['sciezka'] = []

        session.modified = True
        return redirect(url_for('index'))

    poziom = cennik
    for k in session['sciezka']:
        poziom = poziom[k]

    opcje = []
    if isinstance(poziom, dict):
        for k, v in poziom.items():
            opcje.append({
                'nazwa': k,
                'cena': v if isinstance(v, (int, float)) else None,
                'czy_kategoria': isinstance(v, dict)
            })

    suma_koszyka = sum(item['cena'] for item in session['koszyk'])
    liczba_elementow = len(session['koszyk'])

    return render_template(
        'index.html',
        sciezka=session['sciezka'],
        opcje=opcje,
        koszyk=session['koszyk'],
        suma_koszyka=suma_koszyka,
        liczba_elementow=liczba_elementow
    )

@app.route('/koszyk', methods=['GET', 'POST'])
def koszyk():
    if 'koszyk' not in session:
        session['koszyk'] = []

    if request.method == 'POST':
        akcja = request.form.get('akcja')
        
        if akcja == 'wyczysc':
            session['koszyk'] = []
        elif akcja == 'usun':
            index_do_usuniecia = request.form.get('index', type=int)
            aktualny_koszyk = list(session['koszyk'])
            if index_do_usuniecia is not None and 0 <= index_do_usuniecia < len(aktualny_koszyk):
                aktualny_koszyk.pop(index_do_usuniecia)
                session['koszyk'] = aktualny_koszyk
        elif akcja == 'zaplac':
            wplata = float(request.form.get('wplata', 0))
            suma = sum(item['cena'] for item in session['koszyk'])
            if wplata >= suma:
                reszta = wplata - suma
                zaksiegowany_koszyk = list(session['koszyk'])
                session['koszyk'] = []
                return render_template('sukces.html', reszta=reszta, zakupione=zaksiegowany_koszyk)
            else:
                return render_template('koszyk.html', koszyk=session['koszyk'], suma=suma, blad='Niewystarczająca kwota wpłaty!')

        session.modified = True
        return redirect(url_for('koszyk'))

    suma = sum(item['cena'] for item in session['koszyk'])
    return render_template('koszyk.html', koszyk=session['koszyk'], suma=suma)

if __name__ == '__main__':
    app.run(debug=True)