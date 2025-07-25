from privy import PrivyAPI
from config import get_config
import base64

configValues = get_config()

print(configValues.privy.app_id)
print(configValues.privy.app_secret)

app_id = configValues.privy.app_id
app_secret = configValues.privy.app_secret

auth_string = f"{app_id}:{app_secret}"
encoded_auth = base64.b64encode(auth_string.encode()).decode()


client = PrivyAPI(
    app_id="cmdiixr3500b6js0j81dkty6g",
    app_secret="4qgfY9qPy8vzjE4XVzk24y2NzXmvMMtRquQZYJds2kXF1t73g9y7LKzvy7eKsYXC25eurz71TGcrtXXxoMhasLr7",
    environment='staging',
    base_url="https://api.privy.io/"
)

wallet = client.wallets.create(
    chain_type='ethereum'
)

client.wallets.rpc(
    wallet_id=wallet.id,
)

print(wallet)
print(wallet.address)
