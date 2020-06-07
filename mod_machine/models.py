from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Machine(db.Model):
    __tablename__ = 'machine'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(200), nullable=False)
    hostname = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    port = db.Column(db.String(200), nullable=False)
    system = db.Column(db.String(200), nullable=False)
    config = db.relationship('Config', backref='config', uselist=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'hostname': self.hostname,
            'port': self.port,
            'password': self.password,
            'system': self.system,
            'config': self.config.serialize
        }

    def __repr__(self):
        return '<Machine %r' % self.id


class Config(db.Model):
    __tablename__ = 'config'
    id = db.Column(db.Integer, primary_key=True)
    maxMenInPercent = db.Column(db.Integer, nullable=True)
    maxDiscInPercent = db.Column(db.Integer, nullable=True)
    maxCPUInPercent = db.Column(db.Integer, nullable=True)
    email = db.Column(db.String(255), nullable=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'))

    @property
    def serialize(self):
        return {
            'id': self.id,
            'maxMenInPercent': self.maxMenInPercent,
            'maxDiscInPercent': self.maxDiscInPercent,
            'maxCPUInPercent': self.maxCPUInPercent,
            'email': self.email,
            'machine_id': self.machine_id
        }

    def __repr__(self):
        return '<Machine %r' % self.id
