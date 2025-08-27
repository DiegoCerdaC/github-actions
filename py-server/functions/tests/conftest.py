import sys
import types

def _install_fake_firebase():
    # Crea módulos falsos
    fake_fa = types.ModuleType("firebase_admin")
    fake_firestore = types.ModuleType("firebase_admin.firestore")
    fake_credentials = types.ModuleType("firebase_admin.credentials")
    fake_auth = types.ModuleType("firebase_admin.auth")

    # firestore
    fake_firestore.client = lambda *a, **k: object()
    fake_firestore.DocumentReference = types.ModuleType("DocumentReference")

    # credentials
    class _Cert: ...
    fake_credentials.Certificate = lambda *a, **k: _Cert()
    fake_credentials.ApplicationDefault = lambda *a, **k: object()

    # auth
    fake_auth.create_custom_token = lambda uid: b"fake-token"
    fake_auth.verify_id_token = lambda *a, **k: {}

    # raíz firebase_admin
    fake_fa.get_app = lambda *a, **k: object()          # simula app ya existente
    fake_fa.initialize_app = lambda *a, **k: object()   # por si alguien la llama igual
    fake_fa.firestore = fake_firestore
    fake_fa.credentials = fake_credentials
    fake_fa.auth = fake_auth

    # Inyecta en sys.modules ANTES de que se importe utils.firebase
    sys.modules['firebase_admin'] = fake_fa
    sys.modules['firebase_admin.firestore'] = fake_firestore
    sys.modules['firebase_admin.credentials'] = fake_credentials
    sys.modules['firebase_admin.auth'] = fake_auth

def _install_fake_google_cloud():
    """Mock Google Cloud modules to avoid credential errors"""
    # Mock google.cloud.trace
    fake_trace = types.ModuleType("google.cloud.trace")
    fake_trace_v2 = types.ModuleType("google.cloud.trace_v2")
    fake_trace_service = types.ModuleType("google.cloud.trace_v2.services.trace_service")
    fake_transports = types.ModuleType("google.cloud.trace_v2.services.trace_service.transports")
    fake_grpc = types.ModuleType("google.cloud.trace_v2.services.trace_service.transports.grpc")
    
    # Mock the problematic functions
    fake_grpc.TraceServiceGrpcTransport = types.ModuleType("TraceServiceGrpcTransport")
    fake_grpc.TraceServiceGrpcTransport.create_channel = lambda *a, **k: object()
    
    # Mock google.auth
    fake_auth = types.ModuleType("google.auth")
    fake_auth.default = lambda *a, **k: (object(), "fake-project")
    
    # Mock google.api_core
    fake_api_core = types.ModuleType("google.api_core")
    fake_api_core.gapic_v1 = types.ModuleType("google.api_core.gapic_v1")
    fake_api_core.retry = types.ModuleType("google.api_core.retry")
    fake_api_core.retry.retry_base = types.ModuleType("google.api_core.retry.retry_base")
    
    # Mock google.cloud.firestore
    fake_firestore = types.ModuleType("google.cloud.firestore_v1")
    fake_firestore.base_query = types.ModuleType("google.cloud.firestore_v1.base_query")
    fake_firestore.base_query.FieldFilter = object()
    
    # Mock opentelemetry
    fake_opentelemetry = types.ModuleType("opentelemetry")
    fake_exporter = types.ModuleType("opentelemetry.exporter")
    fake_cloud_trace = types.ModuleType("opentelemetry.exporter.cloud_trace")
    
    # Mock CloudTraceSpanExporter
    class FakeCloudTraceSpanExporter:
        def __init__(self, *a, **k):
            pass
    fake_cloud_trace.CloudTraceSpanExporter = FakeCloudTraceSpanExporter
    
    # Inyecta en sys.modules
    sys.modules.setdefault('google.cloud.trace', fake_trace)
    sys.modules.setdefault('google.cloud.trace_v2', fake_trace_v2)
    sys.modules.setdefault('google.cloud.trace_v2.services.trace_service', fake_trace_service)
    sys.modules.setdefault('google.cloud.trace_v2.services.trace_service.transports', fake_transports)
    sys.modules.setdefault('google.cloud.trace_v2.services.trace_service.transports.grpc', fake_grpc)
    sys.modules.setdefault('google.auth', fake_auth)
    sys.modules.setdefault('google.api_core', fake_api_core)
    sys.modules.setdefault('google.api_core.gapic_v1', fake_api_core.gapic_v1)
    sys.modules.setdefault('google.api_core.retry', fake_api_core.retry)
    sys.modules.setdefault('google.api_core.retry.retry_base', fake_api_core.retry.retry_base)
    sys.modules.setdefault('google.cloud.firestore_v1', fake_firestore)
    sys.modules.setdefault('google.cloud.firestore_v1.base_query', fake_firestore.base_query)
    sys.modules.setdefault('opentelemetry.exporter.cloud_trace', fake_cloud_trace)

def _install_fake_services():
    """Mock problematic service modules"""
    # Mock services.tracing
    fake_tracing = types.ModuleType("services.tracing")
    fake_tracing.set_status_ok = lambda *a, **k: None
    fake_tracing.set_status_error = lambda *a, **k: None
    
    # Mock tracer with start_as_current_span decorator
    class FakeTracer:
        def start_as_current_span(self, span_name):
            def decorator(func):
                return func
            return decorator
    
    fake_tracing.tracer = FakeTracer()
    fake_tracing.set_attributes = lambda *a, **k: None
    fake_tracing.init_tracing = lambda *a, **k: None
    
    # Mock utils.firebase
    fake_firebase = types.ModuleType("utils.firebase")
    def mock_get_request_ctx(chat_id, key):
        if key == "function_calls":
            return []
        elif key == "evaluation_mode":
            return False
        elif key == "solana_wallet_address":
            return "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        elif key == "evm_wallet_address":
            return "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
        elif key == "user_id":
            return "test_user_123"
        else:
            return None
    fake_firebase.get_request_ctx = mock_get_request_ctx
    fake_firebase.set_request_ctx = lambda *a, **k: None
    fake_firebase.save_ui_message = lambda *a, **k: None
    fake_firebase.save_agent_thought = lambda *a, **k: None
    fake_firebase.get_top_traders_wallets = lambda *a, **k: ['wallet1', 'wallet2', 'wallet3', 'wallet4', 'wallet5']
    fake_firebase.db = object()  # Mock the db object
    
    # Mock config
    fake_config = types.ModuleType("config")
    fake_config.FIREBASE_SERVER_ENDPOINT = "https://mock-endpoint.com"
    fake_config.SOL_VALIDATORS_API_KEY = "fake-api-key-12345"
    fake_config.LULO_API_KEY = "fake-lulo-api-key-67890"
    fake_config.OPENAI_API_KEY = "fake-openai-api-key"
    
    # Mock services.chains
    fake_chains = types.ModuleType("services.chains")
    fake_chains.call_chains_service = lambda *a, **k: None
    
    # Mock services.tokens
    fake_tokens = types.ModuleType("services.tokens")
    fake_tokens.tokens_service = types.ModuleType("tokens_service")
    fake_tokens.tokens_service.get_token_metadata = lambda *a, **k: None
    
    # Mock services.transactions
    fake_transactions = types.ModuleType("services.transactions")
    fake_transactions.save_transaction_to_db = lambda *a, **k: None
    fake_transactions.TransactionType = types.ModuleType("TransactionType")
    fake_transactions.TransactionType.TRANSFER = types.ModuleType("TRANSFER")
    fake_transactions.TransactionType.TRANSFER.value = "transfer"
    fake_transactions.TransactionType.BRIDGE = types.ModuleType("BRIDGE")
    fake_transactions.TransactionType.BRIDGE.value = "bridge"
    fake_transactions.TransactionType.SWAP = types.ModuleType("SWAP")
    fake_transactions.TransactionType.SWAP.value = "swap"
    fake_transactions.TransactionType.DEPOSIT = types.ModuleType("DEPOSIT")
    fake_transactions.TransactionType.DEPOSIT.value = "deposit"
    fake_transactions.TransactionType.WITHDRAW = types.ModuleType("WITHDRAW")
    fake_transactions.TransactionType.WITHDRAW.value = "withdraw"
    fake_transactions.TransactionType.LIQUIDATION = types.ModuleType("LIQUIDATION")
    fake_transactions.TransactionType.LIQUIDATION.value = "liquidation"
    
    # Mock services.evm_services
    fake_evm_services = types.ModuleType("services.evm_services")
    fake_evm_services.call_evm_blockchains_service = lambda *a, **k: None
    
    # Mock services.balances
    fake_balances = types.ModuleType("services.balances")
    fake_balances.get_single_token_balance = lambda *a, **k: "100.0"
    fake_balances.get_wallet_balance = lambda *a, **k: [
        {
            "wallet_type": "EVM",
            "wallet_address": "0x5eCEBA642dB8f5e7BDa950b7935bBb97209C0bfD",
            "address": "0x0000000000000000000000000000000000000000",
            "chain": "ETHEREUM",
            "name": "Ether",
            "symbol": "ETH",
            "decimals": 18,
            "amount": 0.00000247251228,
            "price": 4394.569,
            "usd_amount": 0.010865625,
            "logo_uri": "https://logos.covalenthq.com/tokens/1/0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.png",
            "protocol": "covalent"
        },
        {
            "wallet_type": "EVM",
            "wallet_address": "0x5eCEBA642dB8f5e7BDa950b7935bBb97209C0bfD",
            "address": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
            "chain": "BASE",
            "name": "USD Coin",
            "symbol": "USDC",
            "decimals": 6,
            "amount": 8.813759,
            "price": 1,
            "usd_amount": 8.813759,
            "logo_uri": "https://logos.covalenthq.com/tokens/8453/0x833589fcd6edb6e08f4c7c32d4f71b54bda02913.png",
            "protocol": "covalent"
        },
        {
            "wallet_type": "EVM",
            "wallet_address": "0x5eCEBA642dB8f5e7BDa950b7935bBb97209C0bfD",
            "address": "0x0000000000000000000000000000000000000000",
            "chain": "BASE",
            "name": "Ether",
            "symbol": "ETH",
            "decimals": 18,
            "amount": 0.000011259972642527,
            "price": 4394.569,
            "usd_amount": 0.049482726,
            "logo_uri": "https://logos.covalenthq.com/tokens/8453/0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.png",
            "protocol": "covalent"
        },
        {
            "wallet_type": "EVM",
            "wallet_address": "0x5eCEBA642dB8f5e7BDa950b7935bBb97209C0bfD",
            "address": "0xfde4c96c8593536e31f229ea8f37b2ada2699bb2",
            "chain": "BASE",
            "name": "Tether USD",
            "symbol": "USDT",
            "decimals": 6,
            "amount": 0.010003,
            "price": 1,
            "usd_amount": 0.010003,
            "logo_uri": "https://logos.covalenthq.com/tokens/8453/0xfde4c96c8593536e31f229ea8f37b2ada2699bb2.png",
            "protocol": "covalent"
        },
        {
            "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v_lulo",
            "amount": 1.016719,
            "name": "USD Coin",
            "chain": "SOLANA",
            "symbol": "USDC - Lulo",
            "decimals": 6,
            "usd_amount": 1.016719,
            "logo_uri": "https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/ethereum/assets/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48/logo.png",
            "wallet_address": "EQZzcSsSzBkxG8fsGGM5FDXJUaJRvvfBgyzC2Qm74r3R",
            "wallet_type": "SOLANA",
            "protocol": "Lulo"
        },
        {
            "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v_drift_vault",
            "amount": 0,
            "name": "USD Coin",
            "chain": "SOLANA",
            "symbol": "USDC - Drift Vault",
            "decimals": 6,
            "usd_amount": 0,
            "logo_uri": "https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/ethereum/assets/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48/logo.png",
            "wallet_address": "EQZzcSsSzBkxG8fsGGM5FDXJUaJRvvfBgyzC2Qm74r3R",
            "wallet_type": "SOLANA",
            "protocol": "Drift"
        }
    ]
    
    fake_balances.BalanceServiceType = types.ModuleType("BalanceServiceType")
    fake_balances.BalanceServiceType.SOLANA = types.ModuleType("SOLANA")
    fake_balances.BalanceServiceType.SOLANA.value = "SOLANA"
    fake_balances.BalanceServiceType.EVM = types.ModuleType("EVM")
    fake_balances.BalanceServiceType.EVM.value = "EVM"
    
    # Mock utils.blockchain_utils
    fake_blockchain_utils = types.ModuleType("utils.blockchain_utils")
    fake_blockchain_utils.is_evm = lambda *a, **k: True
    fake_blockchain_utils.is_solana = lambda *a, **k: True
    
    # Mock utils.bignumber
    fake_bignumber = types.ModuleType("utils.bignumber")
    fake_bignumber.float_to_bignumber_string = lambda *a, **k: "1000000000000000000"
    
    # Mock solders.pubkey
    fake_solders = types.ModuleType("solders")
    fake_solders.pubkey = types.ModuleType("pubkey")
    fake_solders.pubkey.Pubkey = types.ModuleType("Pubkey")
    fake_solders.pubkey.Pubkey.from_string = lambda *a, **k: "fake_pubkey"
    
    # Mock requests
    # Remove the following lines to stop mocking 'requests'
    # fake_requests = types.ModuleType("requests")
    # fake_requests.post = lambda *a, **k: None
    # fake_requests.get = lambda *a, **k: None
    # fake_requests_exceptions = types.ModuleType("requests.exceptions")
    # fake_requests_exceptions.HTTPError = Exception
    # fake_requests_exceptions.RequestException = Exception
    # fake_requests.exceptions = fake_requests_exceptions
    # sys.modules.setdefault('requests', fake_requests)
    # sys.modules.setdefault('requests.exceptions', fake_requests_exceptions)
    
    # Inyecta en sys.modules
    sys.modules.setdefault('services.tracing', fake_tracing)
    sys.modules.setdefault('utils.firebase', fake_firebase)
    sys.modules.setdefault('config', fake_config)
    sys.modules.setdefault('services.chains', fake_chains)
    sys.modules.setdefault('services.tokens', fake_tokens)
    sys.modules.setdefault('services.transactions', fake_transactions)
    sys.modules.setdefault('services.evm_services', fake_evm_services)
    sys.modules.setdefault('services.balances', fake_balances)
    sys.modules.setdefault('utils.blockchain_utils', fake_blockchain_utils)
    sys.modules.setdefault('utils.bignumber', fake_bignumber)
    sys.modules.setdefault('solders.pubkey', fake_solders.pubkey)

def pytest_sessionstart(session):
    _install_fake_firebase()
    _install_fake_google_cloud()
    _install_fake_services()

