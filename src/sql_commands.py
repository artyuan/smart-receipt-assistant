sql_commands = [
    """
    CREATE TABLE invoices (
        invoice_id NUMERIC(44,0) NOT NULL,
        supermarket_name TEXT NOT NULL,
        datetime DATE NOT NULL,
        description TEXT NOT NULL,
        quantity NUMERIC(10,4) NOT NULL,
        unit VARCHAR(10) NOT NULL,
        unitary_value DECIMAL(10,2) NOT NULL,
        total_value DECIMAL(10,2) NOT NULL,
        product TEXT NOT NULL,
        volume VARCHAR(10),
        category TEXT NOT NULL
    );
    """]