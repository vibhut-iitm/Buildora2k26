import qrcode

def generate_qr(token, filename):
    img = qrcode.make(token)
    img.save(filename)