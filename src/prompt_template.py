invoice_prompt = """
    Você receberá abaixo o texto de um **cupom fiscal**. A partir dele, siga **exatamente** os seguintes passos:

    Identifique para **cada item** listado no cupom:
    1. Extrair as seguintes informações para cada item:
        - NÚMERO DO CUPOM FISCAL: código de 44 dígitos que começa com 3525 também chamado de chave de acesso
        - MERCADO (nome do supermercado): como por exemplo Assái, CIA BRASILEIRA DE DISTRIBUICAO
        - DATE (data da compra, formato: DD-MM-AAAA)
        - DESCRIÇÃO (texto completo do item conforme o cupom)
        - QTD (quantidade comprada)
        - UN (unidade de medida: Un, Kg, L, PC, etc.)
        - VL UN R$ (valor unitário)
        - VL ITEM R$ (valor total do item)
        - PRODUTO (nome genérico, como Leite, Detergente, Frango, etc.)
        - PRODUTO MARCA: nome genérico mais a marca, como Leite Italac, Detergente Ypê, Frango Sadia. Quando for produto natural, como alho, cebola, uva, manter apenas o nome.
        - VOLUME (ex: "1L", "500ML", "1KG"; se não houver, usar NULL)
        - CATEGORIA (categoria do produto)

    2. Gerar uma única saída: uma query SQL `INSERT INTO invoices (...) VALUES (...)` que insira todos os produtos extraídos.
        **Regras obrigatórias para a resposta:**
        - A saída deve ser **apenas a query SQL**, sem introduções, sem tabelas e sem explicações, 
        - não inclua a palavra **sql** na query antes do INSERT e não use ```
        - Data deve estar no formato ISO: `AAAA-MM-DD`.
        - Textos entre aspas simples `'`.
        - Números (quantidades, valores) **sem aspas**.
        - Se o volume não existir, use `NULL` (sem aspas).

        **Saída esperada é uma SQL query, não use ponto final - exemplos abaixos são usados apenas para demonstração, valores são ficticios**
        Evite o erro de sintaxe em ou próximo a "." como por exemplo "...,'Utilidades')."
        
        **Exemplo 1**
        INSERT INTO invoices (invoice_id, supermarket_name, datetime, description, quantity, unit, unitary_value, total_value, product, full_product_name, volume, category) VALUES
        (35250447508411271427651040001883521912124444,SuperNova Alimentos,01/01/2023,'LTE ITALAC ZERO 1L',3.00, 'Un', 5.89, 17.60, 'Leite', 'Leite Italac,'1L', 'Laticínios'),
        (35250447508411271427651040001883521912124444,SuperNova Alimentos,01/01/2023,'P QJ SIBERI 1kg TRAD',1.00, 'PC', 14.10, 14.10, 'Pão de Queijo', 'Pão de Queijo Siberi','1KG', 'Padaria e Confeitaria'),
        (35250447508411271427651040001883521912124444,SuperNova Alimentos,01/01/2023,'SASSAMI SADIA 1kg',4.00, 'PC', 20.90, 83.60, 'Frango', 'Frango Sadia','1KG', 'Carnes e Aves');
        
        **Exemplo 2**
        INSERT INTO invoices (invoice_id, supermarket_name, datetime, description, quantity, unit, unitary_value, total_value, product, full_product_name, volume, category) VALUES
        (35250447508411271427651040001874681561004444,VivaBem Supermarket,01/03/2025,'CERV BLUE MOON 350ML',1.00, 'Un', 8.99, 8.99, 'Cerveja', 'Cerveja Blue Moon','350ML', 'Bebidas'),
        (35250447508411271427651040001874681561004444,VivaBem Supermarket,01/03/2025,'ORFEU TM INT 250G ',1.00, 'Un', 38.99, 38.99, 'Cafe', 'Cafe Orfeu','250G', 'Bebidas');
        
        
        
    Cupom fiscal:
    {receipt}
    """