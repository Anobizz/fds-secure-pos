from flask import Flask, render_template, request, redirect, session, url_for
import random

app = Flask(__name__)
app.secret_key = 'fds_secret_key_8583'

DUMMY_CARDS = {
    "5423574876489468": {"expiry": "0926", "cvv": "423", "auth": "451726"}
}
REJECTION_CODES = ["REJ001", "REJ002", "REJ003", "REJ004"]

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/amount', methods=['POST'])
def amount():
    session['amount'] = request.form['amount']
    return render_template('payout.html')

@app.route('/payout', methods=['POST'])
def payout():
    payout_type = request.form['method']
    session['payout_type'] = payout_type
    if payout_type == 'BANK':
        session['bank'] = request.form['bank']
        session['account'] = request.form['account']
    else:
        session['wallet'] = request.form['wallet']
    return render_template('card.html')

@app.route('/card', methods=['POST'])
def card():
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
        return render_template('auth.html')
    else:
        return redirect(url_for('rejected', code=random.choice(REJECTION_CODES)))

@app.route('/auth', methods=['POST'])
def auth():
    code = request.form['auth']
    pan = session.get('pan')
    session['tries'] += 1

    if pan in DUMMY_CARDS and DUMMY_CARDS[pan]['auth'] == code:
        txn_id = random.randint(100000, 999999)
        masked_pan = pan[-4:] if pan else "XXXX"
        return render_template('success.html', txn_id=txn_id, pan=masked_pan)

    elif session['tries'] >= 3:
        reason = "TXN-DENIED-781: AUTH LIMIT"
        session.clear()
        return render_template('rejected.html', code=reason)

    else:
        remaining = 3 - session['tries']
        return render_template('auth.html', warning=f"Wrong code, {remaining} tries left.")

@app.route('/rejected')
def rejected():
    code = request.args.get('code')
    return render_template('rejected.html', code=code)

