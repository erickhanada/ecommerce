"""
Sistema de E-commerce com Azure Cloud
Gerenciamento de produtos, pedidos e imagens com Azure SQL Database e Blob Storage
"""

import os
import hashlib
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from io import BytesIO
import pyodbc
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AzureBlobStorageManager:
    """Gerenciador de armazenamento de imagens no Azure Blob Storage"""
    
    def __init__(self, connection_string: str, container_name: str = "product-images"):
        """
        Inicializa o gerenciador de blob storage
        
        Args:
            connection_string: String de conexão do Azure Storage Account
            container_name: Nome do container para armazenar imagens
        """
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = container_name
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Garante que o container existe, criando-o se necessário"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.create_container()
            logger.info(f"Container '{self.container_name}' criado com sucesso")
        except ResourceExistsError:
            logger.info(f"Container '{self.container_name}' já existe")
        except Exception as e:
            logger.error(f"Erro ao criar/verificar container: {e}")
            raise
    
    def upload_image(self, image_data: bytes, filename: str, content_type: str = "image/jpeg") -> str:
        """
        Faz upload de uma imagem para o blob storage
        
        Args:
            image_data: Dados binários da imagem
            filename: Nome do arquivo
            content_type: Tipo MIME da imagem
            
        Returns:
            URL pública da imagem
        """
        try:
            # Gera nome único para evitar conflitos
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Cria hash MD5 para verificação de integridade
            md5_hash = hashlib.md5(image_data).hexdigest()
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=unique_filename
            )
            
            # Upload com metadados
            blob_client.upload_blob(
                image_data,
                content_settings={
                    'content_type': content_type,
                    'content_md5': md5_hash
                },
                overwrite=True
            )
            
            image_url = blob_client.url
            logger.info(f"Imagem '{unique_filename}' enviada com sucesso")
            return image_url
            
        except Exception as e:
            logger.error(f"Erro ao fazer upload da imagem: {e}")
            raise
    
    def delete_image(self, blob_url: str) -> bool:
        """
        Remove uma imagem do blob storage
        
        Args:
            blob_url: URL completa do blob
            
        Returns:
            True se removido com sucesso
        """
        try:
            # Extrai o nome do blob da URL
            blob_name = blob_url.split('/')[-1]
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            logger.info(f"Imagem '{blob_name}' removida com sucesso")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Imagem não encontrada: {blob_url}")
            return False
        except Exception as e:
            logger.error(f"Erro ao remover imagem: {e}")
            raise
    
    def list_images(self, prefix: str = "") -> List[str]:
        """
        Lista todas as imagens no container
        
        Args:
            prefix: Prefixo para filtrar imagens
            
        Returns:
            Lista de URLs das imagens
        """
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blob_list = container_client.list_blobs(name_starts_with=prefix)
            
            urls = []
            for blob in blob_list:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob.name
                )
                urls.append(blob_client.url)
            
            return urls
        except Exception as e:
            logger.error(f"Erro ao listar imagens: {e}")
            raise


class AzureSQLManager:
    """Gerenciador de banco de dados SQL no Azure"""
    
    def __init__(self, connection_string: str):
        """
        Inicializa o gerenciador de banco de dados
        
        Args:
            connection_string: String de conexão do Azure SQL Database
        """
        self.connection_string = connection_string
        self._initialize_database()
    
    def _get_connection(self):
        """Retorna uma conexão com o banco de dados"""
        return pyodbc.connect(self.connection_string)
    
    def _initialize_database(self):
        """Cria as tabelas necessárias se não existirem"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Tabela de Categorias
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'categories')
                CREATE TABLE categories (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    name NVARCHAR(100) NOT NULL UNIQUE,
                    description NVARCHAR(500),
                    created_at DATETIME2 DEFAULT GETDATE(),
                    updated_at DATETIME2 DEFAULT GETDATE()
                )
            """)
            
            # Tabela de Produtos
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'products')
                CREATE TABLE products (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    name NVARCHAR(200) NOT NULL,
                    description NVARCHAR(MAX),
                    price DECIMAL(10, 2) NOT NULL,
                    stock_quantity INT NOT NULL DEFAULT 0,
                    category_id INT,
                    image_url NVARCHAR(500),
                    sku NVARCHAR(50) UNIQUE,
                    is_active BIT DEFAULT 1,
                    created_at DATETIME2 DEFAULT GETDATE(),
                    updated_at DATETIME2 DEFAULT GETDATE(),
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            """)
            
            # Índice para melhorar performance de busca
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_products_category')
                CREATE INDEX idx_products_category ON products(category_id)
            """)
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_products_sku')
                CREATE INDEX idx_products_sku ON products(sku)
            """)
            
            # Tabela de Clientes
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'customers')
                CREATE TABLE customers (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    name NVARCHAR(200) NOT NULL,
                    email NVARCHAR(200) NOT NULL UNIQUE,
                    phone NVARCHAR(20),
                    address NVARCHAR(500),
                    created_at DATETIME2 DEFAULT GETDATE(),
                    updated_at DATETIME2 DEFAULT GETDATE()
                )
            """)
            
            # Tabela de Pedidos
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'orders')
                CREATE TABLE orders (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    customer_id INT NOT NULL,
                    order_date DATETIME2 DEFAULT GETDATE(),
                    total_amount DECIMAL(10, 2) NOT NULL,
                    status NVARCHAR(50) DEFAULT 'pending',
                    shipping_address NVARCHAR(500),
                    created_at DATETIME2 DEFAULT GETDATE(),
                    updated_at DATETIME2 DEFAULT GETDATE(),
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)
            
            # Tabela de Itens do Pedido
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'order_items')
                CREATE TABLE order_items (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    order_id INT NOT NULL,
                    product_id INT NOT NULL,
                    quantity INT NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    subtotal DECIMAL(10, 2) NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Banco de dados inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    # ========== OPERAÇÕES DE CATEGORIA ==========
    
    def create_category(self, name: str, description: str = None) -> int:
        """Cria uma nova categoria"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO categories (name, description)
                VALUES (?, ?)
            """, (name, description))
            
            cursor.execute("SELECT @@IDENTITY")
            category_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Categoria '{name}' criada com ID {category_id}")
            return category_id
            
        except Exception as e:
            logger.error(f"Erro ao criar categoria: {e}")
            raise
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Retorna todas as categorias"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, description, created_at FROM categories ORDER BY name")
            
            categories = []
            for row in cursor.fetchall():
                categories.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'created_at': row[3]
                })
            
            cursor.close()
            conn.close()
            
            return categories
            
        except Exception as e:
            logger.error(f"Erro ao buscar categorias: {e}")
            raise
    
    # ========== OPERAÇÕES DE PRODUTO ==========
    
    def create_product(self, name: str, description: str, price: float, 
                      stock_quantity: int, category_id: int, 
                      image_url: str = None, sku: str = None) -> int:
        """Cria um novo produto"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if sku is None:
                sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"
            
            cursor.execute("""
                INSERT INTO products (name, description, price, stock_quantity, 
                                    category_id, image_url, sku)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, description, price, stock_quantity, category_id, image_url, sku))
            
            cursor.execute("SELECT @@IDENTITY")
            product_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Produto '{name}' criado com ID {product_id}")
            return product_id
            
        except Exception as e:
            logger.error(f"Erro ao criar produto: {e}")
            raise
    
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Retorna um produto específico"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.id, p.name, p.description, p.price, p.stock_quantity,
                       p.category_id, c.name as category_name, p.image_url, 
                       p.sku, p.is_active, p.created_at
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = ?
            """, (product_id,))
            
            row = cursor.fetchone()
            
            if row:
                product = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'price': float(row[3]),
                    'stock_quantity': row[4],
                    'category_id': row[5],
                    'category_name': row[6],
                    'image_url': row[7],
                    'sku': row[8],
                    'is_active': bool(row[9]),
                    'created_at': row[10]
                }
            else:
                product = None
            
            cursor.close()
            conn.close()
            
            return product
            
        except Exception as e:
            logger.error(f"Erro ao buscar produto: {e}")
            raise
    
    def search_products(self, search_term: str = None, category_id: int = None, 
                       min_price: float = None, max_price: float = None,
                       in_stock_only: bool = False) -> List[Dict[str, Any]]:
        """Busca produtos com filtros"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT p.id, p.name, p.description, p.price, p.stock_quantity,
                       p.category_id, c.name as category_name, p.image_url, 
                       p.sku, p.is_active
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1
            """
            params = []
            
            if search_term:
                query += " AND (p.name LIKE ? OR p.description LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern])
            
            if category_id:
                query += " AND p.category_id = ?"
                params.append(category_id)
            
            if min_price is not None:
                query += " AND p.price >= ?"
                params.append(min_price)
            
            if max_price is not None:
                query += " AND p.price <= ?"
                params.append(max_price)
            
            if in_stock_only:
                query += " AND p.stock_quantity > 0"
            
            query += " ORDER BY p.name"
            
            cursor.execute(query, params)
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'price': float(row[3]),
                    'stock_quantity': row[4],
                    'category_id': row[5],
                    'category_name': row[6],
                    'image_url': row[7],
                    'sku': row[8],
                    'is_active': bool(row[9])
                })
            
            cursor.close()
            conn.close()
            
            return products
            
        except Exception as e:
            logger.error(f"Erro ao buscar produtos: {e}")
            raise
    
    def update_product_stock(self, product_id: int, quantity_change: int) -> bool:
        """Atualiza o estoque de um produto"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE products 
                SET stock_quantity = stock_quantity + ?,
                    updated_at = GETDATE()
                WHERE id = ?
            """, (quantity_change, product_id))
            
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()
            
            if affected_rows > 0:
                logger.info(f"Estoque do produto {product_id} atualizado: {quantity_change:+d}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao atualizar estoque: {e}")
            raise
    
    # ========== OPERAÇÕES DE CLIENTE ==========
    
    def create_customer(self, name: str, email: str, phone: str = None, 
                       address: str = None) -> int:
        """Cria um novo cliente"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO customers (name, email, phone, address)
                VALUES (?, ?, ?, ?)
            """, (name, email, phone, address))
            
            cursor.execute("SELECT @@IDENTITY")
            customer_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Cliente '{name}' criado com ID {customer_id}")
            return customer_id
            
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {e}")
            raise
    
    def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca cliente por email"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, email, phone, address, created_at
                FROM customers
                WHERE email = ?
            """, (email,))
            
            row = cursor.fetchone()
            
            if row:
                customer = {
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'phone': row[3],
                    'address': row[4],
                    'created_at': row[5]
                }
            else:
                customer = None
            
            cursor.close()
            conn.close()
            
            return customer
            
        except Exception as e:
            logger.error(f"Erro ao buscar cliente: {e}")
            raise
    
    # ========== OPERAÇÕES DE PEDIDO ==========
    
    def create_order(self, customer_id: int, items: List[Dict[str, Any]], 
                    shipping_address: str = None) -> int:
        """
        Cria um novo pedido
        
        Args:
            customer_id: ID do cliente
            items: Lista de dicts com 'product_id' e 'quantity'
            shipping_address: Endereço de entrega
            
        Returns:
            ID do pedido criado
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Inicia transação
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Calcula total e valida estoque
                total_amount = 0
                validated_items = []
                
                for item in items:
                    product_id = item['product_id']
                    quantity = item['quantity']
                    
                    # Busca produto e verifica estoque
                    cursor.execute("""
                        SELECT price, stock_quantity, name 
                        FROM products 
                        WHERE id = ? AND is_active = 1
                    """, (product_id,))
                    
                    product = cursor.fetchone()
                    if not product:
                        raise ValueError(f"Produto {product_id} não encontrado ou inativo")
                    
                    price, stock, name = product
                    
                    if stock < quantity:
                        raise ValueError(f"Estoque insuficiente para '{name}'. Disponível: {stock}")
                    
                    subtotal = float(price) * quantity
                    total_amount += subtotal
                    
                    validated_items.append({
                        'product_id': product_id,
                        'quantity': quantity,
                        'unit_price': float(price),
                        'subtotal': subtotal
                    })
                
                # Cria o pedido
                cursor.execute("""
                    INSERT INTO orders (customer_id, total_amount, shipping_address)
                    VALUES (?, ?, ?)
                """, (customer_id, total_amount, shipping_address))
                
                cursor.execute("SELECT @@IDENTITY")
                order_id = cursor.fetchone()[0]
                
                # Adiciona itens do pedido e atualiza estoque
                for item in validated_items:
                    cursor.execute("""
                        INSERT INTO order_items (order_id, product_id, quantity, 
                                                unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                    """, (order_id, item['product_id'], item['quantity'], 
                          item['unit_price'], item['subtotal']))
                    
                    # Atualiza estoque
                    cursor.execute("""
                        UPDATE products 
                        SET stock_quantity = stock_quantity - ?
                        WHERE id = ?
                    """, (item['quantity'], item['product_id']))
                
                cursor.execute("COMMIT TRANSACTION")
                conn.commit()
                
                logger.info(f"Pedido {order_id} criado com sucesso. Total: R$ {total_amount:.2f}")
                return order_id
                
            except Exception as e:
                cursor.execute("ROLLBACK TRANSACTION")
                raise
            
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            logger.error(f"Erro ao criar pedido: {e}")
            raise
    
    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Retorna detalhes completos de um pedido"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Busca pedido
            cursor.execute("""
                SELECT o.id, o.customer_id, c.name as customer_name, c.email,
                       o.order_date, o.total_amount, o.status, o.shipping_address
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.id = ?
            """, (order_id,))
            
            order_row = cursor.fetchone()
            
            if not order_row:
                cursor.close()
                conn.close()
                return None
            
            order = {
                'id': order_row[0],
                'customer_id': order_row[1],
                'customer_name': order_row[2],
                'customer_email': order_row[3],
                'order_date': order_row[4],
                'total_amount': float(order_row[5]),
                'status': order_row[6],
                'shipping_address': order_row[7],
                'items': []
            }
            
            # Busca itens do pedido
            cursor.execute("""
                SELECT oi.id, oi.product_id, p.name, p.sku, oi.quantity,
                       oi.unit_price, oi.subtotal
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (order_id,))
            
            for item_row in cursor.fetchall():
                order['items'].append({
                    'id': item_row[0],
                    'product_id': item_row[1],
                    'product_name': item_row[2],
                    'sku': item_row[3],
                    'quantity': item_row[4],
                    'unit_price': float(item_row[5]),
                    'subtotal': float(item_row[6])
                })
            
            cursor.close()
            conn.close()
            
            return order
            
        except Exception as e:
            logger.error(f"Erro ao buscar pedido: {e}")
            raise
    
    def update_order_status(self, order_id: int, new_status: str) -> bool:
        """Atualiza o status de um pedido"""
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        
        if new_status not in valid_statuses:
            raise ValueError(f"Status inválido. Use: {', '.join(valid_statuses)}")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE orders 
                SET status = ?,
                    updated_at = GETDATE()
                WHERE id = ?
            """, (new_status, order_id))
            
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()
            
            if affected_rows > 0:
                logger.info(f"Status do pedido {order_id} atualizado para '{new_status}'")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status do pedido: {e}")
            raise


class EcommerceCloudSystem:
    """Sistema integrado de e-commerce com Azure"""
    
    def __init__(self, sql_connection_string: str, blob_connection_string: str):
        """
        Inicializa o sistema completo
        
        Args:
            sql_connection_string: String de conexão do Azure SQL
            blob_connection_string: String de conexão do Azure Blob Storage
        """
        self.db = AzureSQLManager(sql_connection_string)
        self.storage = AzureBlobStorageManager(blob_connection_string)
        logger.info("Sistema de e-commerce inicializado com sucesso")
    
    def add_product_with_image(self, name: str, description: str, price: float,
                               stock_quantity: int, category_id: int,
                               image_data: bytes, image_filename: str,
                               sku: str = None) -> int:
        """
        Adiciona um produto com sua imagem
        
        Args:
            name: Nome do produto
            description: Descrição
            price: Preço
            stock_quantity: Quantidade em estoque
            category_id: ID da categoria
            image_data: Dados binários da imagem
            image_filename: Nome do arquivo da imagem
            sku: Código SKU (opcional)
            
        Returns:
            ID do produto criado
        """
        try:
            # Upload da imagem
            image_url = self.storage.upload_image(image_data, image_filename)
            
            # Cria o produto com a URL da imagem
            product_id = self.db.create_product(
                name=name,
                description=description,
                price=price,
                stock_quantity=stock_quantity,
                category_id=category_id,
                image_url=image_url,
                sku=sku
            )
            
            logger.info(f"Produto '{name}' adicionado com imagem")
            return product_id
            
        except Exception as e:
            logger.error(f"Erro ao adicionar produto com imagem: {e}")
            raise
    
    def get_sales_report(self, start_date: datetime = None, 
                        end_date: datetime = None) -> Dict[str, Any]:
        """
        Gera relatório de vendas
        
        Args:
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Dicionário com estatísticas de vendas
        """
        try:
            conn = self.db._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    COUNT(DISTINCT o.id) as total_orders,
                    SUM(o.total_amount) as total_revenue,
                    AVG(o.total_amount) as average_order_value,
                    COUNT(DISTINCT o.customer_id) as unique_customers,
                    SUM(oi.quantity) as total_items_sold
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND o.order_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND o.order_date <= ?"
                params.append(end_date)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            report = {
                'total_orders': row[0] or 0,
                'total_revenue': float(row[1] or 0),
                'average_order_value': float(row[2] or 0),
                'unique_customers': row[3] or 0,
                'total_items_sold': row[4] or 0
            }
            
            cursor.close()
            conn.close()
            
            return report
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            raise


# ========== EXEMPLO DE USO ==========

if __name__ == "__main__":
    # Configurações (substitua com suas credenciais reais)
    SQL_CONNECTION_STRING = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=seu-servidor.database.windows.net;"
        "Database=ecommerce_db;"
        "Uid=seu_usuario;"
        "Pwd=sua_senha;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    
    BLOB_CONNECTION_STRING = (
        "DefaultEndpointsProtocol=https;"
        "AccountName=sua_conta;"
        "AccountKey=sua_chave;"
        "EndpointSuffix=core.windows.net"
    )
    
    # Inicializa o sistema
    ecommerce = EcommerceCloudSystem(SQL_CONNECTION_STRING, BLOB_CONNECTION_STRING)
    
    print("Sistema de E-commerce Azure inicializado com sucesso!")
    print("\nFuncionalidades disponíveis:")
    print("- Gerenciamento de categorias e produtos")
    print("- Upload e armazenamento de imagens no Blob Storage")
    print("- Gerenciamento de clientes e pedidos")
    print("- Controle de estoque automatizado")
    print("- Relatórios de vendas")
    print("- Busca avançada de produtos")
