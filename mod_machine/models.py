from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(200), nullable=False)
    hostname = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    port = db.Column(db.String(200), nullable=False)
    system = db.Column(db.String(200), nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'hostname': self.hostname,
            'port': self.port,
            'password': self.password,
            'system': self.system
        }

    def __repr__(self):
        return '<Machine %r' % self.id