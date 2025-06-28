from flask import Flask, render_template, request, redirect, session, url_for
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'fds_secret_key_8583'

# Dummy card DB
DUMMY_CARDS = {
    "5423574876489468": {"expiry": "0926", "cvv": "423", "auth": "451726"},
    "4444333322221111": {"expiry": "1026", "cvv": "999", "auth": "123456"},
}

REJECTION_CODES = ["REJ001", "REJ002", "REJ003", "REJ004"]

@app.route('/')
def home():
    session.clear()
    return render_template('index.html')

@app.route('/amount', methods=['GET', 'POST'])
def amount():
    if request.method == 'POST':
        session['amount'] = request.form.get('amount')
        return redirect(url_for('payout'))
    return render_template('amount.html')

@app.route('/payout', methods=['GET', 'POST'])
def payout():
    if request.method == 'POST':
        method = request.form.get('method')
        session['payout_type'] = method
        if method == 'BANK':
            session['bank'] = request.form.get('bank')
            session['account'] = request.form.get('account')
        elif method == 'TRC20':
            session['wallet'] = request.form.get('wallet')
        return redirect(url_for('card'))
    return render_template('payout.html')

@app.route('/card', methods=['GET', 'POST'])
def card():
    if request.method == 'POST':
        pan = request.form.get('pan').replace(" ", "")
        exp = request.form.get('expiry').replace("/", "")
        cvv = request.form.get('cvv')

        session['pan'] = pan
        session['exp'] = exp
        session['cvv'] = cvv
        session['tries'] = 0  # reset retry counter

        card = DUMMY_CARDS.get(pan)
        if card:
            if card['expiry'] != exp:
                return redirect(url_for('rejected', code='REJ001'))
            if card['cvv'] != cvv:
                return redirect(url_for('rejected', code='REJ002'))
            return redirect(url_for('auth'))
        else:
            return redirect(url_for('rejected', code=random.choice(REJECTION_CODES)))
    return render_template('card.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    pan = session.get('pan')
    card = DUMMY_CARDS.get(pan)
    tries = session.get('tries', 0)

    if request.method == 'POST':
        code = request.form.get('auth')
        tries += 1
        session['tries'] = tries

        if card and card['auth'] == code:
            txn_id = random.randint(100000, 999999)
            last4 = pan[-4:] if pan else "XXXX"
            return render_template('success.html',
                                   txn_id=txn_id,
                                   pan=last4)
        elif tries >= 3:
            session.clear()
            return redirect(url_for('rejected', code='TXN-DENIED-781: AUTH LIMIT'))
        else:
            remaining = 3 - tries
            return render_template('auth.html',
                                   warning=f"Wrong code. {remaining} tries left.")
    return render_template('auth.html')

@app.route('/rejected')
def rejected():
    code = request.args.get('code', 'TXN-REJECTED')
    return render_template('rejected.html', code=code)

