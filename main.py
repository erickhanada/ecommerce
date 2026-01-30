"""
Script Principal do Sistema de E-commerce Azure
Integra todas as funcionalidades com configuração segura via variáveis de ambiente
"""

from ecommerce_cloud import EcommerceCloudSystem
from config import Config
import sys


def main():
    """Função principal do sistema"""
    
    print("\n" + "=" * 70)
    print("  SISTEMA DE E-COMMERCE COM AZURE CLOUD")
    print("  Gerenciamento Completo de Produtos, Pedidos e Imagens")
    print("=" * 70)
    
    # Valida e exibe configuração
    try:
        print("\n📋 Verificando configuração...")
        Config.print_configuration_info()
        Config.validate_configuration()
        
    except Exception as e:
        print(f"\n❌ Erro na configuração: {e}")
        print("\n💡 Como configurar:")
        print("   1. Copie o arquivo .env.example para .env")
        print("   2. Preencha com suas credenciais do Azure:")
        print("      - Azure SQL Database (servidor, banco, usuário, senha)")
        print("      - Azure Blob Storage (nome da conta, chave de acesso)")
        print("   3. Execute este script novamente\n")
        sys.exit(1)
    
    # Inicializa o sistema
    try:
        print("\n🚀 Inicializando sistema...")
        
        ecommerce = EcommerceCloudSystem(
            sql_connection_string=Config.get_sql_connection_string(),
            blob_connection_string=Config.get_blob_connection_string()
        )
        
        print("✅ Sistema inicializado com sucesso!\n")
        
    except Exception as e:
        print(f"\n❌ Erro ao inicializar sistema: {e}")
        print("   Verifique suas credenciais e conexão com o Azure\n")
        sys.exit(1)
    
    # Menu interativo
    menu_principal(ecommerce)


def menu_principal(ecommerce: EcommerceCloudSystem):
    """Menu interativo do sistema"""
    
    while True:
        print("\n" + "=" * 70)
        print("MENU PRINCIPAL")
        print("=" * 70)
        print("\n📦 PRODUTOS:")
        print("  1. Adicionar categoria")
        print("  2. Listar categorias")
        print("  3. Adicionar produto (sem imagem)")
        print("  4. Adicionar produto (com imagem)")
        print("  5. Buscar produtos")
        print("  6. Atualizar estoque")
        
        print("\n👥 CLIENTES:")
        print("  7. Cadastrar cliente")
        print("  8. Buscar cliente por email")
        
        print("\n🛒 PEDIDOS:")
        print("  9. Criar pedido")
        print("  10. Consultar pedido")
        print("  11. Atualizar status do pedido")
        
        print("\n📊 RELATÓRIOS:")
        print("  12. Relatório de vendas")
        print("  13. Produtos com estoque baixo")
        
        print("\n💾 ARMAZENAMENTO:")
        print("  14. Listar imagens no Blob Storage")
        
        print("\n0. Sair")
        print("=" * 70)
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == '0':
            print("\n👋 Encerrando sistema. Até logo!")
            break
        
        elif opcao == '1':
            adicionar_categoria(ecommerce)
        
        elif opcao == '2':
            listar_categorias(ecommerce)
        
        elif opcao == '3':
            adicionar_produto_simples(ecommerce)
        
        elif opcao == '4':
            adicionar_produto_com_imagem(ecommerce)
        
        elif opcao == '5':
            buscar_produtos(ecommerce)
        
        elif opcao == '6':
            atualizar_estoque(ecommerce)
        
        elif opcao == '7':
            cadastrar_cliente(ecommerce)
        
        elif opcao == '8':
            buscar_cliente(ecommerce)
        
        elif opcao == '9':
            criar_pedido(ecommerce)
        
        elif opcao == '10':
            consultar_pedido(ecommerce)
        
        elif opcao == '11':
            atualizar_status_pedido(ecommerce)
        
        elif opcao == '12':
            relatorio_vendas(ecommerce)
        
        elif opcao == '13':
            produtos_estoque_baixo(ecommerce)
        
        elif opcao == '14':
            listar_imagens(ecommerce)
        
        else:
            print("\n❌ Opção inválida. Tente novamente.")
        
        input("\nPressione ENTER para continuar...")


# ========== FUNÇÕES DO MENU ==========

def adicionar_categoria(ecommerce: EcommerceCloudSystem):
    """Adiciona uma nova categoria"""
    print("\n--- ADICIONAR CATEGORIA ---")
    
    nome = input("Nome da categoria: ").strip()
    descricao = input("Descrição: ").strip()
    
    try:
        categoria_id = ecommerce.db.create_category(nome, descricao)
        print(f"\n✅ Categoria '{nome}' criada com sucesso! (ID: {categoria_id})")
    except Exception as e:
        print(f"\n❌ Erro ao criar categoria: {e}")


def listar_categorias(ecommerce: EcommerceCloudSystem):
    """Lista todas as categorias"""
    print("\n--- CATEGORIAS CADASTRADAS ---")
    
    try:
        categorias = ecommerce.db.get_categories()
        
        if not categorias:
            print("\nNenhuma categoria cadastrada.")
            return
        
        print(f"\nTotal: {len(categorias)} categoria(s)\n")
        for cat in categorias:
            print(f"ID: {cat['id']}")
            print(f"Nome: {cat['name']}")
            print(f"Descrição: {cat['description'] or 'N/A'}")
            print("-" * 50)
    except Exception as e:
        print(f"\n❌ Erro ao listar categorias: {e}")


def adicionar_produto_simples(ecommerce: EcommerceCloudSystem):
    """Adiciona um produto sem imagem"""
    print("\n--- ADICIONAR PRODUTO (SEM IMAGEM) ---")
    
    nome = input("Nome do produto: ").strip()
    descricao = input("Descrição: ").strip()
    
    try:
        preco = float(input("Preço (R$): ").strip())
        estoque = int(input("Quantidade em estoque: ").strip())
        categoria_id = int(input("ID da categoria: ").strip())
    except ValueError:
        print("\n❌ Valor inválido. Use números para preço, estoque e ID da categoria.")
        return
    
    sku = input("SKU (deixe em branco para gerar automaticamente): ").strip() or None
    
    try:
        produto_id = ecommerce.db.create_product(
            name=nome,
            description=descricao,
            price=preco,
            stock_quantity=estoque,
            category_id=categoria_id,
            sku=sku
        )
        print(f"\n✅ Produto '{nome}' criado com sucesso! (ID: {produto_id})")
    except Exception as e:
        print(f"\n❌ Erro ao criar produto: {e}")


def adicionar_produto_com_imagem(ecommerce: EcommerceCloudSystem):
    """Adiciona um produto com imagem"""
    print("\n--- ADICIONAR PRODUTO (COM IMAGEM) ---")
    
    nome = input("Nome do produto: ").strip()
    descricao = input("Descrição: ").strip()
    
    try:
        preco = float(input("Preço (R$): ").strip())
        estoque = int(input("Quantidade em estoque: ").strip())
        categoria_id = int(input("ID da categoria: ").strip())
    except ValueError:
        print("\n❌ Valor inválido.")
        return
    
    caminho_imagem = input("Caminho da imagem: ").strip()
    sku = input("SKU (deixe em branco para gerar automaticamente): ").strip() or None
    
    try:
        # Lê o arquivo de imagem
        with open(caminho_imagem, 'rb') as f:
            imagem_data = f.read()
        
        # Extrai o nome do arquivo
        import os
        nome_arquivo = os.path.basename(caminho_imagem)
        
        produto_id = ecommerce.add_product_with_image(
            name=nome,
            description=descricao,
            price=preco,
            stock_quantity=estoque,
            category_id=categoria_id,
            image_data=imagem_data,
            image_filename=nome_arquivo,
            sku=sku
        )
        print(f"\n✅ Produto '{nome}' criado com imagem! (ID: {produto_id})")
    except FileNotFoundError:
        print(f"\n❌ Arquivo não encontrado: {caminho_imagem}")
    except Exception as e:
        print(f"\n❌ Erro ao criar produto: {e}")


def buscar_produtos(ecommerce: EcommerceCloudSystem):
    """Busca produtos com filtros"""
    print("\n--- BUSCAR PRODUTOS ---")
    
    termo = input("Termo de busca (deixe em branco para listar todos): ").strip() or None
    categoria_id = input("ID da categoria (deixe em branco para todas): ").strip()
    categoria_id = int(categoria_id) if categoria_id else None
    
    try:
        produtos = ecommerce.db.search_products(
            search_term=termo,
            category_id=categoria_id
        )
        
        if not produtos:
            print("\nNenhum produto encontrado.")
            return
        
        print(f"\n{len(produtos)} produto(s) encontrado(s):\n")
        for p in produtos:
            print(f"ID: {p['id']} | SKU: {p['sku']}")
            print(f"Nome: {p['name']}")
            print(f"Preço: R$ {p['price']:.2f}")
            print(f"Estoque: {p['stock_quantity']} unidades")
            print(f"Categoria: {p['category_name']}")
            if p['image_url']:
                print(f"Imagem: {p['image_url'][:60]}...")
            print("-" * 70)
    except Exception as e:
        print(f"\n❌ Erro ao buscar produtos: {e}")


def atualizar_estoque(ecommerce: EcommerceCloudSystem):
    """Atualiza o estoque de um produto"""
    print("\n--- ATUALIZAR ESTOQUE ---")
    
    try:
        produto_id = int(input("ID do produto: ").strip())
        quantidade = int(input("Quantidade a adicionar/remover (use - para remover): ").strip())
        
        sucesso = ecommerce.db.update_product_stock(produto_id, quantidade)
        
        if sucesso:
            print(f"\n✅ Estoque atualizado! ({quantidade:+d} unidades)")
        else:
            print("\n❌ Produto não encontrado.")
    except ValueError:
        print("\n❌ Valor inválido.")
    except Exception as e:
        print(f"\n❌ Erro ao atualizar estoque: {e}")


def cadastrar_cliente(ecommerce: EcommerceCloudSystem):
    """Cadastra um novo cliente"""
    print("\n--- CADASTRAR CLIENTE ---")
    
    nome = input("Nome completo: ").strip()
    email = input("Email: ").strip()
    telefone = input("Telefone: ").strip() or None
    endereco = input("Endereço: ").strip() or None
    
    try:
        cliente_id = ecommerce.db.create_customer(nome, email, telefone, endereco)
        print(f"\n✅ Cliente '{nome}' cadastrado com sucesso! (ID: {cliente_id})")
    except Exception as e:
        print(f"\n❌ Erro ao cadastrar cliente: {e}")


def buscar_cliente(ecommerce: EcommerceCloudSystem):
    """Busca cliente por email"""
    print("\n--- BUSCAR CLIENTE ---")
    
    email = input("Email do cliente: ").strip()
    
    try:
        cliente = ecommerce.db.get_customer_by_email(email)
        
        if cliente:
            print(f"\n✅ Cliente encontrado:")
            print(f"ID: {cliente['id']}")
            print(f"Nome: {cliente['name']}")
            print(f"Email: {cliente['email']}")
            print(f"Telefone: {cliente['phone'] or 'N/A'}")
            print(f"Endereço: {cliente['address'] or 'N/A'}")
        else:
            print(f"\n❌ Cliente não encontrado com o email: {email}")
    except Exception as e:
        print(f"\n❌ Erro ao buscar cliente: {e}")


def criar_pedido(ecommerce: EcommerceCloudSystem):
    """Cria um novo pedido"""
    print("\n--- CRIAR PEDIDO ---")
    
    try:
        cliente_id = int(input("ID do cliente: ").strip())
        endereco = input("Endereço de entrega: ").strip()
        
        itens = []
        while True:
            print("\nAdicionar item ao pedido:")
            produto_id = int(input("  ID do produto (0 para finalizar): ").strip())
            
            if produto_id == 0:
                break
            
            quantidade = int(input("  Quantidade: ").strip())
            itens.append({'product_id': produto_id, 'quantity': quantidade})
        
        if not itens:
            print("\n❌ Nenhum item adicionado ao pedido.")
            return
        
        pedido_id = ecommerce.db.create_order(cliente_id, itens, endereco)
        print(f"\n✅ Pedido criado com sucesso! (ID: {pedido_id})")
        
    except ValueError:
        print("\n❌ Valor inválido.")
    except Exception as e:
        print(f"\n❌ Erro ao criar pedido: {e}")


def consultar_pedido(ecommerce: EcommerceCloudSystem):
    """Consulta detalhes de um pedido"""
    print("\n--- CONSULTAR PEDIDO ---")
    
    try:
        pedido_id = int(input("ID do pedido: ").strip())
        
        pedido = ecommerce.db.get_order(pedido_id)
        
        if not pedido:
            print(f"\n❌ Pedido não encontrado: {pedido_id}")
            return
        
        print(f"\n📦 PEDIDO #{pedido['id']}")
        print(f"Cliente: {pedido['customer_name']} ({pedido['customer_email']})")
        print(f"Data: {pedido['order_date']}")
        print(f"Status: {pedido['status']}")
        print(f"Endereço: {pedido['shipping_address']}")
        print(f"Total: R$ {pedido['total_amount']:.2f}")
        print("\nItens:")
        
        for item in pedido['items']:
            print(f"  - {item['product_name']} (SKU: {item['sku']})")
            print(f"    Qtd: {item['quantity']} x R$ {item['unit_price']:.2f} = R$ {item['subtotal']:.2f}")
        
    except ValueError:
        print("\n❌ ID inválido.")
    except Exception as e:
        print(f"\n❌ Erro ao consultar pedido: {e}")


def atualizar_status_pedido(ecommerce: EcommerceCloudSystem):
    """Atualiza o status de um pedido"""
    print("\n--- ATUALIZAR STATUS DO PEDIDO ---")
    print("\nStatus disponíveis: pending, processing, shipped, delivered, cancelled")
    
    try:
        pedido_id = int(input("\nID do pedido: ").strip())
        novo_status = input("Novo status: ").strip().lower()
        
        sucesso = ecommerce.db.update_order_status(pedido_id, novo_status)
        
        if sucesso:
            print(f"\n✅ Status do pedido {pedido_id} atualizado para '{novo_status}'")
        else:
            print("\n❌ Pedido não encontrado.")
    except ValueError:
        print("\n❌ ID inválido ou status inválido.")
    except Exception as e:
        print(f"\n❌ Erro ao atualizar status: {e}")


def relatorio_vendas(ecommerce: EcommerceCloudSystem):
    """Gera relatório de vendas"""
    print("\n--- RELATÓRIO DE VENDAS ---")
    
    try:
        relatorio = ecommerce.get_sales_report()
        
        print("\n📊 ESTATÍSTICAS DE VENDAS")
        print("=" * 50)
        print(f"Total de pedidos: {relatorio['total_orders']}")
        print(f"Receita total: R$ {relatorio['total_revenue']:.2f}")
        print(f"Ticket médio: R$ {relatorio['average_order_value']:.2f}")
        print(f"Clientes únicos: {relatorio['unique_customers']}")
        print(f"Itens vendidos: {relatorio['total_items_sold']}")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Erro ao gerar relatório: {e}")


def produtos_estoque_baixo(ecommerce: EcommerceCloudSystem):
    """Lista produtos com estoque baixo"""
    print("\n--- PRODUTOS COM ESTOQUE BAIXO ---")
    
    try:
        limite = int(input("Limite de estoque (padrão: 10): ").strip() or "10")
        
        produtos = ecommerce.db.search_products()
        produtos_baixo = [p for p in produtos if p['stock_quantity'] < limite]
        
        if not produtos_baixo:
            print(f"\n✅ Nenhum produto com estoque abaixo de {limite} unidades.")
            return
        
        print(f"\n⚠️  {len(produtos_baixo)} produto(s) com estoque baixo:\n")
        for p in produtos_baixo:
            print(f"ID: {p['id']} | SKU: {p['sku']}")
            print(f"Nome: {p['name']}")
            print(f"Estoque: {p['stock_quantity']} unidades")
            print("-" * 50)
    except ValueError:
        print("\n❌ Valor inválido.")
    except Exception as e:
        print(f"\n❌ Erro ao buscar produtos: {e}")


def listar_imagens(ecommerce: EcommerceCloudSystem):
    """Lista todas as imagens no Blob Storage"""
    print("\n--- IMAGENS NO BLOB STORAGE ---")
    
    try:
        imagens = ecommerce.storage.list_images()
        
        if not imagens:
            print("\nNenhuma imagem armazenada.")
            return
        
        print(f"\nTotal: {len(imagens)} imagem(ns)\n")
        for i, url in enumerate(imagens, 1):
            print(f"{i}. {url}")
    except Exception as e:
        print(f"\n❌ Erro ao listar imagens: {e}")


if __name__ == "__main__":
    main()
