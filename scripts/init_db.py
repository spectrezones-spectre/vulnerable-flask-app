import sqlite3, os, hashlib
BASE=os.path.dirname(os.path.dirname(__file__)); DB=os.path.join(BASE,'lab.db')
if os.path.exists(DB): os.remove(DB)
con=sqlite3.connect(DB); cur=con.cursor()
cur.executescript('''
CREATE TABLE roles(id INTEGER PRIMARY KEY, name TEXT UNIQUE, description TEXT);
CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, email TEXT, role_id INTEGER, FOREIGN KEY(role_id) REFERENCES roles(id));
CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, description TEXT, category TEXT, price REAL, stock INTEGER);
CREATE TABLE audit_log(id INTEGER PRIMARY KEY, event TEXT, actor TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
''')
cur.executemany('INSERT INTO roles VALUES (?,?,?)',[(1,'user','Utilisateur standard'),(2,'analyst','Analyste sécurité'),(3,'admin','Administrateur de l’application')])
cur.executemany('INSERT INTO users(username,password,email,role_id) VALUES (?,?,?,?)',[
 ('alice','alice123','alice@lab.local',1),('bob','bob123','bob@lab.local',1),('analyst','observe123','analyst@lab.local',2),('admin','admin123','admin@lab.local',3)])
products=[('Router Atlas','Routeur pédagogique double bande','network',79.90,12),('Switch Copper','Commutateur 8 ports','network',44.50,20),('Firewall Ember','Pare-feu de démonstration','security',129.00,5),('Scanner Nova','Scanner de ports local','security',59.00,8),('Keyboard Quartz','Clavier mécanique','hardware',72.00,15),('Monitor Prism','Écran 24 pouces','hardware',189.00,7),('USB Lab Key','Clé USB de test','hardware',12.90,40),('Proxy Lantern','Proxy HTTP pédagogique','security',99.00,6)]
cur.executemany('INSERT INTO products(name,description,category,price,stock) VALUES (?,?,?,?,?)',products)
cur.execute("INSERT INTO audit_log(event,actor) VALUES ('Database initialized','system')")
con.commit(); con.close(); print(f'Base réinitialisée: {DB}')
