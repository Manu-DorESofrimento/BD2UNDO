#imports
import re


from scripts.print_out import print_transactions, print_json, print_update



def find_committed_transactions(file):
    committed_transactions = set()
    file.seek(0)

    for line in file:
        matches = re.search('<(start|commit) (.+?)>', line)
        if matches:
            action, transaction = matches.group(1), matches.group(2)
            if action=='commit':
                # Se a transação não foi confirmada deve ser desfeita
                committed_transactions.add(transaction)
    
    return list(committed_transactions)

def find_uncommitted_transactions(file, committed_transactions):
    # Encontra transações que não foram confirmadas
    uncommitted_transactions = set()
    file.seek(0)

    for line in file:
        matches = re.search('<(start|commit) (.+?)>', line)
        if matches:
            action, transaction = matches.group(1), matches.group(2)
            if transaction not in committed_transactions:
                # Se a transação não foi confirmada deve ser desfeita
                uncommitted_transactions.add(transaction)
    
    return list(uncommitted_transactions)

def restore_changes(file, cursor, committed_transactions, uncommitted_transactions):
    # Percorre transações commitadas e não confirmadas
    for transaction in committed_transactions + uncommitted_transactions:
        # Retorna para o início do arquivo
        file.seek(0)

        # Vai para o início da transação
        content = file.read()
        start_transaction = content.index(f'<start {transaction}>')
        file.seek(start_transaction)

        # Percorre o arquivo do início da transação até o final
        for line in file:
            # Quando chegar no commit ou rollback da transição, para
            if f'<commit {transaction}>' in line or f'<rollback {transaction}>' in line:
                break
            
            matches = re.search(f'<{transaction},(.+?)>', line)
            # Se for log da transação, atualiza no banco
            if matches:
                # Cria um array com os valores informados no arquivo de log
                values = matches.group(1).split(',')
                
                # Retorna a coluna da tupla com o ID informado no arquivo
                cursor.execute(f'SELECT {values[1]} FROM data WHERE id = {values[0]}')
                tuple_value = cursor.fetchone()[0]

                # Confere se o valor que está no arquivo é diferente do valor que está no BD
                if int(values[2]) != tuple_value:
                    cursor.execute(f'UPDATE data SET {values[1]} = {values[2]} WHERE id = {values[0]}')
                    print_update(transaction, tuple_value, values)

def perform_undo(cursor):
    with open('test_files/entradaLog', 'r') as file:
        try:
            # Pega transações que foram committadas após o checkpoint
            committed_transactions = find_committed_transactions(file)

            # Encontra transações não confirmadas ou desfeitas
            uncommitted_transactions = find_uncommitted_transactions(file, committed_transactions)
            
            print(committed_transactions)
            print(uncommitted_transactions)
            # Restaurar mudanças feitas nas transações commitadas e não confirmadas
            restore_changes(file, cursor, committed_transactions, uncommitted_transactions)

            # Imprime saída
            print_transactions(committed_transactions, uncommitted_transactions)
            print_json(cursor)

        finally:
            pass

