"""
Configuração do Sistema de E-commerce
Carrega credenciais de variáveis de ambiente de forma segura
"""

import os
from dotenv import load_dotenv
from typing import Optional

# Carrega variáveis do arquivo .env
load_dotenv()


class Config:
    """Classe de configuração centralizada"""
    
    # ========== CONFIGURAÇÃO SQL DATABASE ==========
    
    @staticmethod
    def get_sql_connection_string() -> str:
        """
        Retorna a connection string do Azure SQL Database
        
        Prioridade:
        1. Variável SQL_CONNECTION_STRING (connection string completa)
        2. Variáveis individuais (SERVER, DATABASE, USERNAME, PASSWORD)
        """
        
        # Opção 1: Connection string completa
        conn_str = os.getenv('SQL_CONNECTION_STRING')
        if conn_str:
            return conn_str
        
        # Opção 2: Construir a partir de variáveis individuais
        server = os.getenv('AZURE_SQL_SERVER')
        database = os.getenv('AZURE_SQL_DATABASE')
        username = os.getenv('AZURE_SQL_USERNAME')
        password = os.getenv('AZURE_SQL_PASSWORD')
        driver = os.getenv('AZURE_SQL_DRIVER', 'ODBC Driver 18 for SQL Server')
        
        if not all([server, database, username, password]):
            raise ValueError(
                "Configuração SQL incompleta. Configure as variáveis de ambiente:\n"
                "- SQL_CONNECTION_STRING (ou)\n"
                "- AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD"
            )
        
        return (
            f"Driver={{{driver}}};"
            f"Server={server},1433;"
            f"Database={database};"
            f"Uid={username};"
            f"Pwd={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
    
    # ========== CONFIGURAÇÃO BLOB STORAGE ==========
    
    @staticmethod
    def get_blob_connection_string() -> str:
        """
        Retorna a connection string do Azure Blob Storage
        
        Prioridade:
        1. Variável BLOB_CONNECTION_STRING (connection string completa)
        2. Variáveis individuais (ACCOUNT_NAME, ACCOUNT_KEY)
        """
        
        # Opção 1: Connection string completa
        conn_str = os.getenv('BLOB_CONNECTION_STRING')
        if conn_str:
            return conn_str
        
        # Opção 2: Construir a partir de variáveis individuais
        account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
        account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
        
        if not all([account_name, account_key]):
            raise ValueError(
                "Configuração Blob Storage incompleta. Configure as variáveis de ambiente:\n"
                "- BLOB_CONNECTION_STRING (ou)\n"
                "- AZURE_STORAGE_ACCOUNT_NAME, AZURE_STORAGE_ACCOUNT_KEY"
            )
        
        return (
            f"DefaultEndpointsProtocol=https;"
            f"AccountName={account_name};"
            f"AccountKey={account_key};"
            f"EndpointSuffix=core.windows.net"
        )
    
    @staticmethod
    def get_blob_container_name() -> str:
        """Retorna o nome do container para imagens"""
        return os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'product-images')
    
    # ========== VALIDAÇÃO ==========
    
    @staticmethod
    def validate_configuration() -> bool:
        """
        Valida se todas as configurações necessárias estão presentes
        
        Returns:
            True se configuração válida, levanta exceção caso contrário
        """
        try:
            Config.get_sql_connection_string()
            Config.get_blob_connection_string()
            return True
        except ValueError as e:
            print(f"❌ Erro de configuração: {e}")
            raise
    
    # ========== INFORMAÇÕES ==========
    
    @staticmethod
    def print_configuration_info():
        """Imprime informações sobre a configuração (sem expor senhas)"""
        print("=" * 60)
        print("CONFIGURAÇÃO DO SISTEMA")
        print("=" * 60)
        
        try:
            # SQL Database
            sql_server = os.getenv('AZURE_SQL_SERVER', 'N/A')
            sql_database = os.getenv('AZURE_SQL_DATABASE', 'N/A')
            
            print(f"\n📊 Azure SQL Database:")
            print(f"  Servidor: {sql_server}")
            print(f"  Banco de dados: {sql_database}")
            
            # Blob Storage
            storage_account = os.getenv('AZURE_STORAGE_ACCOUNT_NAME', 'N/A')
            container = Config.get_blob_container_name()
            
            print(f"\n💾 Azure Blob Storage:")
            print(f"  Storage Account: {storage_account}")
            print(f"  Container: {container}")
            
            print("\n✅ Configuração carregada com sucesso!")
            
        except Exception as e:
            print(f"\n❌ Erro ao carregar configuração: {e}")
            print("\n📝 Para configurar:")
            print("  1. Copie .env.example para .env")
            print("  2. Preencha com suas credenciais do Azure")
            print("  3. Execute o script novamente")


# ========== EXEMPLO DE USO ==========

if __name__ == "__main__":
    # Tenta carregar e validar a configuração
    try:
        Config.print_configuration_info()
        Config.validate_configuration()
        
        print("\n" + "=" * 60)
        print("Configuração válida! Sistema pronto para uso.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Falha na configuração: {e}")
        print("\nVerifique o arquivo .env e tente novamente.")
