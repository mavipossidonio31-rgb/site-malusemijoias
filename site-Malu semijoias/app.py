from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_malu_semijoias_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ==================== MODELOS DA BASE DE DADOS ====================

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    endereco_completo = db.Column(db.Text, nullable=False)
    pedidos = db.relationship('Pedido', backref='cliente', lazy=True)


class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    produtos = db.relationship('Produto', backref='categoria', lazy=True)


class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=0)
    imagem_url = db.Column(db.String(255), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Novo Pedido')
    forma_pagamento = db.Column(db.String(50), nullable=False)
    total = db.Column(db.Float, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True)


class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    produto = db.relationship('Produto')


# ==================== ROTAS DE AUTENTICAÇÃO E NAVEGAÇÃO ====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    tipo = request.form.get('tipo_usuario')
    email = request.form.get('email')
    senha = request.form.get('senha')

    if tipo == 'admin':
        if email == 'admin@malu.com' and senha == 'admin123':
            session['user_type'] = 'admin'
            return redirect(url_for('admin'))
        flash('Credenciais de Administrador incorretas!')
    else:
        cliente = Cliente.query.filter_by(email=email, senha=senha).first()
        if cliente:
            session['user_type'] = 'cliente'
            session['cliente_id'] = cliente.id
            session['cliente_nome'] = cliente.nome_completo
            return redirect(url_for('produtos'))
        flash('E-mail ou senha incorretos!')

    return redirect(url_for('index'))


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        novo_cliente = Cliente(
            nome_completo=request.form['nome_completo'],
            email=request.form['email'],
            senha=request.form['senha'],
            telefone=request.form['telefone'],
            endereco_completo=request.form['endereco_completo']
        )
        db.session.add(novo_cliente)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Faça login.')
        return redirect(url_for('index'))
    return render_template('cadastro.html')


@app.route('/produtos')
def produtos():
    categorias = Categoria.query.all()
    return render_template('produtos.html', categorias=categorias)


@app.route('/carrinho')
def carrinho():
    cliente_id = session.get('cliente_id')
    pedidos_cliente = []

    # Busca os pedidos do cliente logado ordenados do mais recente ao mais antigo
    if cliente_id:
        pedidos_cliente = Pedido.query.filter_by(cliente_id=cliente_id).order_by(Pedido.data.desc()).all()

    return render_template('carrinho.html', pedidos_cliente=pedidos_cliente)


@app.route('/contato')
def contato():
    return render_template('contato.html')


@app.route('/sobre')
def sobre():
    return render_template('sobre.html')


@app.route('/finalizar_pedido', methods=['POST'])
def finalizar_pedido():
    if session.get('user_type') != 'cliente':
        return jsonify({'success': False, 'message': 'Você precisa estar logado para realizar um pedido.'}), 401

    dados = request.get_json()
    itens_carrinho = dados.get('itens', [])
    forma_pagamento = dados.get('forma_pagamento', 'Pix')

    if not itens_carrinho:
        return jsonify({'success': False, 'message': 'Carrinho vazio.'}), 400

    total_pedido = sum(item['preco'] * item.get('quantidade', 1) for item in itens_carrinho)

    novo_pedido = Pedido(
        forma_pagamento=forma_pagamento,
        total=total_pedido,
        cliente_id=session['cliente_id'],
        status='Novo Pedido'
    )
    db.session.add(novo_pedido)
    db.session.commit()

    for item in itens_carrinho:
        item_pedido = ItemPedido(
            pedido_id=novo_pedido.id,
            produto_id=item['id'],
            quantidade=item.get('quantidade', 1),
            preco_unitario=item['preco']
        )
        db.session.add(item_pedido)

        prod = Produto.query.get(item['id'])
        if prod and prod.estoque >= item.get('quantidade', 1):
            prod.estoque -= item.get('quantidade', 1)

    db.session.commit()
    return jsonify({'success': True, 'pedido_id': novo_pedido.id})


# ==================== ROTAS DO PAINEL ADMIN ====================

@app.route('/admin')
def admin():
    if session.get('user_type') != 'admin':
        return redirect(url_for('index'))

    termo_busca = request.args.get('busca_cliente', '').strip()

    if termo_busca:
        pedidos = Pedido.query.join(Cliente).filter(
            Cliente.nome_completo.ilike(f'%{termo_busca}%')
        ).order_by(Pedido.data.desc()).all()
    else:
        pedidos = Pedido.query.order_by(Pedido.data.desc()).all()

    produtos = Produto.query.all()
    clientes = Cliente.query.all()
    categorias = Categoria.query.all()

    lucro_total = sum(p.total for p in pedidos if p.status != 'Cancelado')

    return render_template('admin.html',
                           pedidos=pedidos,
                           produtos=produtos,
                           clientes=clientes,
                           categorias=categorias,
                           lucro_total=lucro_total,
                           termo_busca=termo_busca)


@app.route('/admin/adicionar_produto', methods=['POST'])
def adicionar_produto():
    if session.get('user_type') != 'admin':
        return redirect(url_for('index'))

    novo_prod = Produto(
        nome=request.form['nome'],
        preco=float(request.form['preco']),
        estoque=int(request.form['estoque']),
        categoria_id=int(request.form['categoria_id']),
        imagem_url=request.form['imagem_url']
    )
    db.session.add(novo_prod)
    db.session.commit()
    flash('Produto adicionado à base de dados com sucesso!')
    return redirect(url_for('admin'))


@app.route('/admin/atualizar_status', methods=['POST'])
def atualizar_status_pedido():
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403

    dados = request.get_json()
    pedido = Pedido.query.get(dados.get('pedido_id'))

    if pedido:
        pedido.status = dados.get('status')
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Pedido não encontrado'}), 404


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ==================== BANCO DE DADOS E POVOAMENTO ====================

def popular_banco():
    db.create_all()

    if not Categoria.query.first():
        cat_brincos = Categoria(nome="Brincos")
        cat_colares = Categoria(nome="Colares")
        cat_aneis = Categoria(nome="Anéis")
        cat_pulseiras = Categoria(nome="Pulseiras")
        cat_conjuntos = Categoria(nome="Conjuntos")

        db.session.add_all([cat_brincos, cat_colares, cat_aneis, cat_pulseiras, cat_conjuntos])
        db.session.commit()

        lista_produtos = [
            # --- ANÉIS ---
            Produto(nome="Anel Aboulé Cravejado Luxo", preco=189.90, estoque=12, categoria_id=cat_aneis.id,
                    imagem_url="/static/img/anel1.jpg"),
            Produto(nome="Anel Espiral Orgânico Zircônias", preco=169.90, estoque=10, categoria_id=cat_aneis.id,
                    imagem_url="/static/img/anel2.jpg"),
            Produto(nome="Anel Solitário Prata 925 Oval", preco=210.00, estoque=8, categoria_id=cat_aneis.id,
                    imagem_url="/static/img/anel3.jpg"),
            Produto(nome="Anel Flor Buquê Esmeralda 18k", preco=198.00, estoque=14, categoria_id=cat_aneis.id,
                    imagem_url="/static/img/anel4.jpg"),
            Produto(nome="Anel Solitário Cristal Extra Grande", preco=229.00, estoque=6, categoria_id=cat_aneis.id,
                    imagem_url="/static/img/anel5.jpg"),
            Produto(nome="Anel Entrelocado Rubi & Zircônias", preco=179.90, estoque=11, categoria_id=cat_aneis.id,
                    imagem_url="/static/img/anel6.jpg"),
            Produto(nome="Anel Meia Aliança Cravejado Ouro", preco=149.90, estoque=15, categoria_id=cat_aneis.id,
                    imagem_url="/static/img/anel7.jpg"),
            Produto(nome="Anel Pavê Gota Zircônia Cristal", preco=159.00, estoque=9, categoria_id=cat_aneis.id,
                    imagem_url="/static/img/anel8.jpg"),
            Produto(nome="Anel Duplo Geométrico Banhado", preco=139.90, estoque=13, categoria_id=cat_aneis.id,
                    imagem_url="/static/img/anel9.jpg"),
            Produto(nome="Anel Coração Cristal Prata 925", preco=169.00, estoque=7, categoria_id=cat_aneis.id,
                    imagem_url="/static/img/anel10.jpg"),

            # --- BRINCOS ---
            Produto(nome="Brinco Botão Madrepérola Ouro 18k", preco=139.90, estoque=15, categoria_id=cat_brincos.id,
                    imagem_url="/static/img/brinco1.jpg"),
            Produto(nome="Brinco Gota Clássica Zircônia", preco=149.00, estoque=18, categoria_id=cat_brincos.id,
                    imagem_url="/static/img/brinco2.jpg"),
            Produto(nome="Brinco Ear Cuff Leque Navetes", preco=159.90, estoque=9, categoria_id=cat_brincos.id,
                    imagem_url="/static/img/brinco3.jpg"),
            Produto(nome="Brinco Ear Cuff Cristais Fake", preco=135.00, estoque=12, categoria_id=cat_brincos.id,
                    imagem_url="/static/img/brinco4.jpg"),
            Produto(nome="Brinco Trio Zircônia Laranja", preco=165.00, estoque=8, categoria_id=cat_brincos.id,
                    imagem_url="/static/img/brinco5.jpg"),
            Produto(nome="Brinco Perla Clássico Ouro 18k", preco=119.00, estoque=13, categoria_id=cat_brincos.id,
                    imagem_url="/static/img/brinco6.jpg"),
            Produto(nome="Brinco Argola Banhada Ouro 18k", preco=129.90, estoque=20, categoria_id=cat_brincos.id,
                    imagem_url="/static/img/brinco7.jpg"),
            Produto(nome="Brinco Leve Cravejado Luxo", preco=99.90, estoque=16, categoria_id=cat_brincos.id,
                    imagem_url="/static/img/brinco8.jpg"),
            Produto(nome="Brinco Argola Tripla Cravejada", preco=145.00, estoque=10, categoria_id=cat_brincos.id,
                    imagem_url="/static/img/brinco9.jpg"),
            Produto(nome="Brinco Gota Zircônia Cristal", preco=139.00, estoque=14, categoria_id=cat_brincos.id,
                    imagem_url="/static/img/brinco10.jpg"),

            # --- COLARES ---
            Produto(nome="Colar Gravatinha Ponto de Luz", preco=189.90, estoque=12, categoria_id=cat_colares.id,
                    imagem_url="/static/img/colar1.jpg"),
            Produto(nome="Colar Choker Malha Banhada 18k", preco=169.00, estoque=15, categoria_id=cat_colares.id,
                    imagem_url="/static/img/colar2.jpg"),
            Produto(nome="Colar Pingente Coração Zircônia", preco=145.00, estoque=10, categoria_id=cat_colares.id,
                    imagem_url="/static/img/colar3.jpg"),
            Produto(nome="Colar Relicário Elegance Ouro", preco=210.00, estoque=7, categoria_id=cat_colares.id,
                    imagem_url="/static/img/colar4.jpg"),
            Produto(nome="Colar Duplo Camadas Cristais", preco=199.90, estoque=9, categoria_id=cat_colares.id,
                    imagem_url="/static/img/colar5.jpg"),
            Produto(nome="Gargantilha Fita Banhada Ouro", preco=179.90, estoque=14, categoria_id=cat_colares.id,
                    imagem_url="/static/img/colar6.jpg"),
            Produto(nome="Colar Gota Azul Royale 18k", preco=185.00, estoque=11, categoria_id=cat_colares.id,
                    imagem_url="/static/img/colar7.jpg"),
            Produto(nome="Colar Choker Elo Português", preco=159.90, estoque=13, categoria_id=cat_colares.id,
                    imagem_url="/static/img/colar8.jpg"),
            Produto(nome="Colar Riviera Zircônia Transparente", preco=220.00, estoque=6, categoria_id=cat_colares.id,
                    imagem_url="/static/img/colar9.jpg"),
            Produto(nome="Colar Medalha Solitária Ouro", preco=169.90, estoque=8, categoria_id=cat_colares.id,
                    imagem_url="/static/img/colar10.jpg"),

            # --- PULSEIRAS ---
            Produto(nome="Pulseira Elo Português Banhada", preco=149.00, estoque=16, categoria_id=cat_pulseiras.id,
                    imagem_url="/static/img/pulseira1.jpg"),
            Produto(nome="Pulseira Riviera Zircônias", preco=189.00, estoque=11, categoria_id=cat_pulseiras.id,
                    imagem_url="/static/img/pulseira2.jpg"),
            Produto(nome="Pulseira Berloques & Pedras", preco=199.90, estoque=8, categoria_id=cat_pulseiras.id,
                    imagem_url="/static/img/pulseira3.jpg"),
            Produto(nome="Pulseira Corrente Grumet 18k", preco=165.00, estoque=13, categoria_id=cat_pulseiras.id,
                    imagem_url="/static/img/pulseira4.jpg"),
            Produto(nome="Pulseira Delicada Ponto de Luz", preco=125.00, estoque=22, categoria_id=cat_pulseiras.id,
                    imagem_url="/static/img/pulseira5.jpg"),
            Produto(nome="Pulseira Regulável Olho Grego", preco=139.90, estoque=17, categoria_id=cat_pulseiras.id,
                    imagem_url="/static/img/pulseira6.jpg"),
            Produto(nome="Pulseira Tubo Rígida Banhada", preco=179.00, estoque=10, categoria_id=cat_pulseiras.id,
                    imagem_url="/static/img/pulseira7.jpg"),
            Produto(nome="Pulseira Algema Cravejada Luxo", preco=210.00, estoque=5, categoria_id=cat_pulseiras.id,
                    imagem_url="/static/img/pulseira8.jpg"),
            Produto(nome="Pulseira Cordão Baiano Ouro 18k", preco=155.00, estoque=14, categoria_id=cat_pulseiras.id,
                    imagem_url="/static/img/pulseira9.jpg"),
            Produto(nome="Pulseira Tripla Zircônias Cristais", preco=185.00, estoque=9, categoria_id=cat_pulseiras.id,
                    imagem_url="/static/img/pulseira10.jpg"),

            # --- CONJUNTOS ---
            Produto(nome="Conjunto Gota Verde Esmeralda", preco=289.00, estoque=6, categoria_id=cat_conjuntos.id,
                    imagem_url="/static/img/conjunto1.jpg"),
            Produto(nome="Conjunto Brinco/Colar Azul Royale", preco=299.00, estoque=5, categoria_id=cat_conjuntos.id,
                    imagem_url="/static/img/conjunto2.jpg"),
            Produto(nome="Conjunto Coração Cravejado Ouro", preco=279.90, estoque=8, categoria_id=cat_conjuntos.id,
                    imagem_url="/static/img/conjunto3.jpg"),
            Produto(nome="Conjunto Ponto de Luz Zircônia", preco=249.00, estoque=10, categoria_id=cat_conjuntos.id,
                    imagem_url="/static/img/conjunto4.jpg"),
            Produto(nome="Conjunto Geometric Fita & Argolas", preco=310.00, estoque=4, categoria_id=cat_conjuntos.id,
                    imagem_url="/static/img/conjunto5.jpg"),
            Produto(nome="Conjunto Pérola & Cristais", preco=269.00, estoque=7, categoria_id=cat_conjuntos.id,
                    imagem_url="/static/img/conjunto6.jpg"),
            Produto(nome="Conjunto Flor Safira & Brincos", preco=320.00, estoque=3, categoria_id=cat_conjuntos.id,
                    imagem_url="/static/img/conjunto7.jpg"),
            Produto(nome="Conjunto Gravatinha & Anel Luxo", preco=295.00, estoque=6, categoria_id=cat_conjuntos.id,
                    imagem_url="/static/img/conjunto8.jpg"),
            Produto(nome="Conjunto Gota Rubi Banhado 18k", preco=305.00, estoque=5, categoria_id=cat_conjuntos.id,
                    imagem_url="/static/img/conjunto9.jpg"),
            Produto(nome="Conjunto Riviera Completo Ouro", preco=349.90, estoque=4, categoria_id=cat_conjuntos.id,
                    imagem_url="/static/img/conjunto10.jpg")
        ]

        db.session.add_all(lista_produtos)

        cliente_exemplo = Cliente(
            nome_completo="Maria Silva",
            email="maria@exemplo.com",
            senha="123",
            telefone="(19) 99999-8888",
            endereco_completo="Rua das Flores, 123 - Centro"
        )
        db.session.add(cliente_exemplo)
        db.session.commit()

        pedido_exemplo = Pedido(
            forma_pagamento="Pix",
            total=278.90,
            cliente_id=cliente_exemplo.id,
            status="Sendo Preparado"
        )
        db.session.add(pedido_exemplo)
        db.session.commit()


# ==================== INICIALIZAÇÃO DO SERVIDOR ====================

if __name__ == '__main__':
    with app.app_context():
        popular_banco()
    app.run(debug=True)