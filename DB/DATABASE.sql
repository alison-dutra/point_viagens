DROP DATABASE point_viagens;
CREATE DATABASE point_viagens;
USE point_viagens;



CREATE TABLE cadastro_cliente (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(100) NOT NULL,
    nascimento VARCHAR(100) NOT NULL,
    celular VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL
);

CREATE TABLE cadastro_afiliado (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome_afiliado VARCHAR(100) NOT NULL,
    cpf VARCHAR(100) NOT NULL,
    rg VARCHAR(100) NOT NULL,
    endereço VARCHAR(100) NOT NULL,
    celular VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE
);

CREATE TABLE produtos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome_produto VARCHAR(100) NOT NULL,
    categoria_id INT,
    marca VARCHAR(100),
    preco DECIMAL(10, 2),
    descricao TEXT,
    imagem_url VARCHAR(500),
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE vendas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    codigo_venda VARCHAR(100) NOT NULL,
    cliente_id INT NOT NULL,
    afiliado_id INT NOT NULL,
    produto_id INT NOT NULL,
    descricao_venda VARCHAR(100) NOT NULL,
    tipo_venda VARCHAR(100) NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_venda ENUM('pendente', 'reprovado', 'aprovado') DEFAULT 'pendente',
    CONSTRAINT fk_vendas_cliente FOREIGN KEY (cliente_id) REFERENCES cadastro_cliente(id),
    CONSTRAINT fk_vendas_afiliado FOREIGN KEY (afiliado_id) REFERENCES cadastro_afiliado(id),
    CONSTRAINT fk_vendas_produto FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

CREATE TABLE comissoes_pagamentos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    afiliado_id INT NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    data_pagamento DATE NOT NULL,
    descricao TEXT,
    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comissao_afiliado FOREIGN KEY (afiliado_id) REFERENCES cadastro_afiliado(id)
);

select * from cadastro_cliente
select * from cadastro_afiliado
select * from vendas
select * from comissoes_pagamentos
select * from produtos


CREATE TABLE afiliado_documentos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    afiliado_id INT NOT NULL,
    arquivo VARCHAR(500) NOT NULL,
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_doc_afiliado FOREIGN KEY (afiliado_id) REFERENCES cadastro_afiliado(id)
);
