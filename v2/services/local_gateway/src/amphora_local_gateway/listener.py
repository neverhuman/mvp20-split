"""Explicit local or private IPv4 HTTPS boundary; peer services always stay loopback."""
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
import ssl
from .errors import require

PRIVATE=(IPv4Network('10.0.0.0/8'),IPv4Network('172.16.0.0/12'),IPv4Network('192.168.0.0/16'))

@dataclass(frozen=True)
class Listener:
    address:str='127.0.0.1'
    subnet:str='127.0.0.0/8'
    certificate:Path|None=None
    private_key:Path|None=None

    @property
    def secure(self):return self.certificate is not None

    @classmethod
    def load(cls,value):
        require(type(value) is dict and set(value)=={'address','subnet','certificate','private_key'},'gateway_listener_shape')
        address=IPv4Address(value['address']);network=IPv4Network(value['subnet'],strict=True)
        require(str(address)==value['address'] and str(network)==value['subnet'] and
                any(address in p and network.subnet_of(p) for p in PRIVATE) and
                16<=network.prefixlen<=30 and address in network and
                address not in (network.network_address,network.broadcast_address),'gateway_listener_scope')
        paths=[Path(value[n]) for n in ('certificate','private_key')]
        require(all(p.is_absolute() and p.is_file() for p in paths),'gateway_tls_files')
        return cls(str(address),str(network),*paths)

    def allows(self,address):
        try:return IPv4Address(address) in IPv4Network(self.subnet)
        except ValueError:return False

    def origin(self,port):return ('https' if self.secure else 'http')+'://'+self.address+':'+str(port)

    def tls(self):
        if not self.secure:return None
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version=ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(self.certificate,self.private_key)
        return context
