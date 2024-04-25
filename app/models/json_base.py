from dataclasses import dataclass, field
from datetime import datetime
from random import randint, seed, shuffle
from firebase_admin import credentials, db, initialize_app  # type: ignore
from typing import Union
import pytz  # type: ignore
import json
import os
import shutil
import uuid


tz = pytz.timezone('America/Sao_Paulo')


def firebase_init(json_name: str, url_db: str):
    cred = credentials.Certificate(
        f"./app/models/auth/{json_name}")
    initialize_app(cred, {
        'databaseURL': f'{url_db}'
    })


firebase_init(
    'auth.json',
    'https://seudb-rtdb.firebaseio.com/'
)


@dataclass
class User:
    nickname: str
    password: str
    server_name: str = 'chat'
    friends: list = field(default_factory=list, repr=False, init=False)
    user: str = 'Privado'
    today: str = datetime.now(tz).strftime('%d/%m/%Y')
    refuser = db.reference('users')

    def encrypt(self, server, se_ed):
        server = list(server)
        seed(se_ed)
        shuffle(server)
        return ''.join(server)

    def user_server_name_set(self, server_name: str):
        user = self.refuser.order_by_child(
            'nickname').equal_to(self.nickname).get()
        if not user:
            self.refuser.push({
                'username': self.user,
                'nickname': self.nickname,
                'password': self.password,
                'last_login': self.today,
                'server_name': server_name,
            })
        else:
            for key, value in user.items():
                self.refuser.child(key).update({
                    'server_name': server_name,
                    'last_login': self.today,
                })
                self.server_name = value['server_name']

    @property
    def user_server_name_extract(self):
        user = self.refuser.order_by_child(
            'nickname').equal_to(self.nickname).get()
        if user:
            for value in user.values():
                server_name = value['server_name']
                if server_name == 'None'\
                    or server_name is None\
                    or server_name == ''\
                    or server_name == 'chat'\
                        or self.user_last_login_check != self.today:
                    try:
                        self.delete_db(server_name)
                    except Exception:
                        pass
                    self.user_server_name_set(
                        f'{randint(11111, 99999)}_{self.user.replace(
                            " ", "_").lower()}')
                self.server_name = server_name

    @property
    def user_last_login_check(self):
        user = self.refuser.order_by_child(
            'nickname').equal_to(self.nickname).get()
        if user:
            for value in user.values():
                return value['last_login']

    def add_friend(self, friend_nickname):
        friend_nickname = friend_nickname.lower()
        # Verifique se o amigo já está na lista de amigos
        friend_home = f'{randint(11111, 99999)}_{friend_nickname}_{self.user}'
        if friend_nickname not in self.get_friends:
            # Adicione o amigo à lista de amigos
            # print(f'{friend_nickname} não é seu amigo.')
            # Atualize a lista de amigos no banco de dados

            friend = self.refuser.order_by_child(
                'nickname').equal_to(friend_nickname).get()
            friend_key = None
            if friend:
                for key in friend.keys():
                    friend_username = friend[key].get('username')
                    friend_nickname = friend[key].get('nickname')
                    friend_key = key
                    # print(friend_username, friend_key)

            if friend_key is None:
                return None

            self.friends[friend_nickname] = {
                'private_room': friend_home,
                'id': friend_key,
                'username': friend_username,
                'nickname': friend_nickname
                }

            user = self.refuser.order_by_child(
                'nickname').equal_to(self.nickname).get()
            if user:
                for key in user.keys():
                    user_key = key
                    self.refuser.child(key).update({
                        'friends': self.friends,
                    })

            # Adicione o usuário atual à lista de amigos do amigo
            friend = self.refuser.order_by_child(
                'nickname').equal_to(friend_nickname).get()
            if friend:
                for key in friend.keys():
                    friend_friends = friend[key].get('friends', {})
                    if self.nickname not in friend_friends:
                        friend_friends[self.nickname] = {
                            'private_room': friend_home,
                            'id': user_key,
                            'username': self.user,
                            'nickname': self.nickname
                            }
                        self.refuser.child(key).update({
                            'friends': friend_friends,
                        })

            # print(f'{friend_nickname} adicionado à lista de amigos.')
        # else:
        #     # print(f"{friend_nickname} já é seu amigo.")

    def change_password(self, last_password, new_password):
        user = self.refuser.order_by_child(
            'nickname').equal_to(self.nickname).get()
        if user:
            for key in user.keys():
                if user[key]['password'] == last_password:
                    self.refuser.child(key).update({
                        'password': new_password,
                    })
                    return True
        return False

    @property
    def get_friends(self):
        user = self.refuser.order_by_child(
            'nickname').equal_to(self.nickname).get()

        if user:
            for value in user.values():
                if 'friends' in value:
                    self.friends = value['friends']
                else:
                    self.friends = {}
                return self.friends

    def delete_friend(self, friend_nickname):
        friend_nickname = friend_nickname.lower()
        # Verifique se o amigo já está na lista de amigos
        if friend_nickname in self.get_friends:
            # Remova o amigo da lista de amigos
            del self.friends[friend_nickname]
            # Atualize a lista de amigos no banco de dados
            user = self.refuser.order_by_child(
                'nickname').equal_to(self.nickname).get()
            if user:
                for key in user.keys():
                    self.refuser.child(key).update({
                        'friends': self.friends,
                    })

            # Remova o usuário atual da lista de amigos do amigo
            friend = self.refuser.order_by_child(
                'nickname').equal_to(friend_nickname).get()
            if friend:
                for key in friend.keys():
                    friend_friends = friend[key].get('friends', {})
                    # print(friend_friends)
                    if self.nickname in friend_friends:
                        del friend_friends[self.nickname]
                        self.refuser.child(key).update({
                            'friends': friend_friends,
                        })

            # print(f'{friend_nickname} removido da lista de amigos.')
        # else:
        #     print(f"{friend_nickname} não é seu amigo.")

    def delete_db(self, server_name: str):

        file_path = f'app/chat/{self.encrypt(server_name.lower(), 40028922)}/{self.encrypt(server_name.lower(), 40028922)}.json'  # noqa

        diretorio = os.path.dirname(file_path)

        # Verifica se o diretório existe
        if not os.path.exists(diretorio):
            # Cria o diretório
            os.makedirs(diretorio)

        backup_path = f'app/chat/.backup/{
            self.encrypt(server_name.lower(), 40028922)
            }.json'

        # Faz backup das mensagens
        if os.path.exists(file_path):
            shutil.copyfile(file_path, backup_path)

        # Deleta as mensagens
        if os.path.exists(file_path):
            os.remove(file_path)

    def notification_private_home(self, friend_nickname):
        friend_nickname = friend_nickname.lower()
        user = self.refuser.order_by_child(
            'nickname').equal_to(friend_nickname).get()
        if user:
            for value in user.values():
                return value['friends'][self.nickname]['private_room']

    def verificar_se_existe_nova_mensagem(self, private_room: str):
        # Define o caminho do arquivo
        file_path = f'app/chat/{self.encrypt(private_room.lower(), 40028922)}/{self.encrypt(private_room.lower(), 40028922)}.json'  # noqa

        diretorio = os.path.dirname(file_path)

        # Verifica se o diretório existe
        if not os.path.exists(diretorio):
            # Cria o diretório
            os.makedirs(diretorio)

        # Carrega as mensagens existentes
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            if data is not None:
                for message in data:
                    for key in message.keys():
                        if message[key]['username'] != self.user\
                              and message[key]['read'] is False:
                            return True
        return False

    def verificar_lastmsg(self, private_room: str):
        # Define o caminho do arquivo
        file_path = f'app/chat/{self.encrypt(private_room.lower(), 40028922)}/{self.encrypt(private_room.lower(), 40028922)}.json'  # noqa

        diretorio = os.path.dirname(file_path)

        # Verifica se o diretório existe
        if not os.path.exists(diretorio):
            # Cria o diretório
            os.makedirs(diretorio)

        # Carrega as mensagens existentes
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Conte o número de mensagens na sala privada
            num_messages = len(data) if data else 0

            return num_messages
        else:
            return 0

    def get_private_room_read(self, my_nickname: str) -> bool:
        user = self.refuser.order_by_child(
            'nickname').equal_to(my_nickname).get()
        if user:
            for value in user.values():
                if 'friends' in value:
                    for friend in value['friends'].values():
                        if 'private_room' in friend:
                            private_room = friend['private_room']
                            file_path = f'app/chat/{self.encrypt(private_room.lower(), 40028922)}/{self.encrypt(private_room.lower(), 40028922)}.json'  # noqa

                            diretorio = os.path.dirname(file_path)

                            # Verifica se o diretório existe
                            if not os.path.exists(diretorio):
                                # Cria o diretório
                                os.makedirs(diretorio)
                            # Carrega as mensagens existentes
                            if os.path.exists(file_path):
                                with open(file_path, 'r') as f:
                                    data = json.load(f)
                                if data:
                                    # Obter a última mensagem
                                    last_message = list(data[-1].values())[0]
                                    if 'read' in last_message\
                                            and 'username' in last_message:

                                        if not last_message['read']\
                                              and last_message['username'] != self.user:  # noqa
                                            return True
        return False

    def get_private_room_last_message(self, my_nickname: str) -> dict:
        def msg_filter(msg, username):
            if "<img" in msg and username != self.user:
                return "Imagem recebida"
            elif "<img" in msg and username == self.user:
                return "Imagem enviada"
            elif "<video" in msg and username != self.user:
                return "Vídeo recebido"
            elif "<video" in msg and username == self.user:
                return "Vídeo enviado"
            elif "<audio" in msg and username != self.user:
                return "Áudio recebido"
            elif "<audio" in msg and username == self.user:
                return "Áudio enviado"
            elif "<button" in msg and username != self.user:
                return "Arquivo recebido"
            elif "<button" in msg and username == self.user:
                return "Arquivo enviado"
            elif "class='respostas'" in msg and username != self.user:
                return "Resposta recebida"
            elif "class='respostas'" in msg and username == self.user:
                return "Resposta enviada"
            elif "Mensagem apagada</em>" in msg:
                return "Mensagem apagada"
            return msg

        result = {}
        user = self.refuser.order_by_child(
            'nickname').equal_to(my_nickname).get()
        if user:
            for value in user.values():
                if 'friends' in value:
                    for friend in value['friends'].values():
                        # print(friend)
                        if 'private_room' in friend:
                            private_room = friend['private_room']
                            # print(private_room)
                            file_path = f'app/chat/{self.encrypt(private_room.lower(), 40028922)}/{self.encrypt(private_room.lower(), 40028922)}.json'  # noqa

                            diretorio = os.path.dirname(file_path)

                            # Verifica se o diretório existe
                            if not os.path.exists(diretorio):
                                # Cria o diretório
                                os.makedirs(diretorio)

                            # Carrega as mensagens existentes
                            if os.path.exists(file_path):
                                with open(file_path, 'r') as f:
                                    chat_room = json.load(f)
                                if chat_room:
                                    # Obter a última mensagem
                                    last_message = list(chat_room[-1].values())[0]  # noqa
                                    if 'message' in last_message:
                                        result[private_room] = {
                                            'friend': friend['username'],
                                            'friendnickname': friend['nickname'],  # noqa
                                            'friendid': friend['id'],
                                            'lastmsg': msg_filter(last_message['message'], last_message['username']),  # noqa
                                            'whosend': last_message['username'],  # noqa
                                            'time': last_message['hora'],
                                            'date': last_message.get('data', ''),  # noqa
                                            'read': last_message['read']
                                        }
                                # print(result)

            # Converte o dicionário em uma lista de tuplas
            result_items = list(result.items())

            # Ordena a lista de tuplas pela data e hora
            result_items.sort(
                key=lambda item: (item[1]['time'], item[1]['date']
                                  ), reverse=True)

            # Converte a lista de tuplas de volta em um dicionário
            result = dict(result_items)

        return result

    @property
    def get_all_private_room_names(self):
        user = self.refuser.order_by_child(
            'nickname').equal_to(self.nickname).get()
        private_rooms = []
        if user:
            for value in user.values():
                if 'friends' in value:
                    for friend in value['friends'].values():
                        if 'private_room' in friend:
                            private_rooms.append(
                                friend['private_room'].lower())

        return private_rooms

    def save_last_server_name(self):
        privates = []
        user = self.refuser.order_by_child(
            'nickname').equal_to(self.nickname).get()
        if user:
            for value in user.values():
                if 'friends' in value:
                    for friend in value['friends'].values():
                        if 'private_room' in friend:
                            privates.append(friend['private_room'])

            for key in user.keys():
                # Recupera a lista atual de servidores
                last_server_name = user[key].get('last_server_name', [])

                # Adiciona o novo servidor à lista
                last_server_name.append(self.server_name) if self.server_name not in last_server_name\
                    and self.server_name not in privates\
                    and self.server_name not in self.get_all_private_room_names else None  # noqa

                # Atualiza o banco de dados com a nova lista
                self.refuser.child(key).update({
                    'last_server_name': last_server_name,
                })

    def get_last_server_name(self):
        user = self.refuser.order_by_child(
            'nickname').equal_to(self.nickname).get()
        if user:
            for value in user.values():
                return value.get('last_server_name', [])

    def delete_one_last_server_name(self, server_name: str):
        user = self.refuser.order_by_child(
            'nickname').equal_to(self.nickname).get()
        if user:
            for key in user.keys():
                last_server_name = user[key].get('last_server_name', [])
                last_server_name.remove(server_name) if server_name in last_server_name else None  # noqa
                self.refuser.child(key).update({
                    'last_server_name': last_server_name,
                })

    def delete_msg_do_private_room(self, private_room: str):
        # Define o caminho do arquivo
        file_path = f'app/chat/{self.encrypt(private_room.lower(), 40028922)}/{self.encrypt(private_room.lower(), 40028922)}.json'  # noqa

        diretorio = os.path.dirname(file_path)

        # Verifica se o diretório existe
        if not os.path.exists(diretorio):
            # Cria o diretório
            os.makedirs(diretorio)

        # Verifica se o arquivo existe
        if os.path.exists(file_path):
            os.remove(file_path)


@dataclass
class SecureChat:
    user: User
    ban_user: list = field(default_factory=list, repr=False, init=False)
    mensagens: list = field(default_factory=list, repr=False, init=False)
    file_path: str = ''

    def __post_init__(self):
        def encrypt(server, se_ed):
            server = list(server)
            seed(se_ed)
            shuffle(server)
            return ''.join(server)

        self.file_path = f'./app/data/chat/{encrypt(self.user.server_name.lower(), 40028922)}/{encrypt(self.user.server_name.lower(), 40028922)}.json'   # noqa

        diretorio = os.path.dirname(self.file_path)

        if not os.path.exists(diretorio):
            if encrypt(self.user.server_name.lower(), 40028922) != 'ahtc':
                os.makedirs(diretorio)

        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                if f.read().strip():
                    f.seek(0)  # Reset the file pointer to the beginning
                    data = json.load(f)
                    if data is not None:
                        self.mensagens.extend(data)

        self.ban_user = []

    def encrypt(self, server, se_ed):
        server = list(server)
        seed(se_ed)
        shuffle(server)
        return ''.join(server)

    def get_chat_messages(self, user: User):
        result = []
        # Carrega mensagens existentes
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                self.mensagens = json.load(f)
        else:
            self.mensagens = []

        for mensagem in self.mensagens:
            for key, i in mensagem.items():
                if i['username'] != user.user:
                    i['read'] = True
                    # Atualiza a mensagem para 'read'
                    mensagem[key] = {
                        'username': i['username'],
                        'message': i['message'],
                        'hora': i['hora'],
                        'dia': i['dia'],
                        'data': i['data'],
                        'id': i['id'],
                        'read': True
                    }
                result.append(i)

        # Salva mensagens
        with open(self.file_path, 'w') as f:
            json.dump(self.mensagens, f)

        return result

    def is_user_valid(self, user: User):
        # print(user.server_name, 'secure_chat')
        if user.user in self.ban_user:
            return False
        return True

    def add_message(self, message: str, usuario):
        def day():
            if datetime.now(tz).strftime('%a') == 'Mon':
                return 'seg'
            elif datetime.now(tz).strftime('%a') == 'Tue':
                return 'ter'
            elif datetime.now(tz).strftime('%a') == 'Wed':
                return 'qua'
            elif datetime.now(tz).strftime('%a') == 'Thu':
                return 'qui'
            elif datetime.now(tz).strftime('%a') == 'Fri':
                return 'sex'
            elif datetime.now(tz).strftime('%a') == 'Sat':
                return 'sáb'
            elif datetime.now(tz).strftime('%a') == 'Sun':
                return 'dom'

        if self.is_user_valid(self.user):
            new_message = {}
            id = str(uuid.uuid4())
            print(id)
            new_message[id] = {
                'username': usuario,
                'message': message,
                'hora': f"{datetime.now(tz).strftime(f'%H:%M')}",
                'dia': f"{day()}",
                'data': f"{datetime.now(tz).strftime('%d/%m/%Y')}",
                'id': id,  # Gera um ID aleatório
                'read': False
            }

            # Carrega mensagens existentes
            # print('Carregando mensagens existentes')
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    self.mensagens = json.load(f)
            else:
                self.mensagens = []

            # Adiciona nova mensagem
            # print('Adicionando nova mensagem')
            self.mensagens.append(new_message)

            # Salva mensagens
            # print('Salvando mensagens')
            with open(self.file_path, 'w') as f:
                json.dump(self.mensagens, f)

            return True
        else:
            return False

    def delete_db(self, cod):
        if cod == 'delete':
            backup_file_path = f'app/chat/.backup/{
                self.encrypt(self.user.server_name.lower(), 40028922)}.json'
            # Faz backup das mensagens
            if os.path.exists(backup_file_path):
                # Carrega mensagens do backup
                with open(backup_file_path, 'r') as f:
                    backup_mensagens = json.load(f)
            else:
                backup_mensagens = []

            # Adiciona mensagens atuais ao backup
            backup_mensagens.extend(self.mensagens)

            # Salva o backup
            with open(backup_file_path, 'w') as f:
                json.dump(backup_mensagens, f)

            # Deleta as mensagens
            if os.path.exists(self.file_path):
                os.remove(self.file_path)

            self.mensagens = []

    def delete_message(self, id: int):
        # Carrega mensagens existentes
        print('Carregando mensagens existentes')
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                self.mensagens = json.load(f)
        else:
            self.mensagens = []

        for mensagem in self.mensagens:
            for key, i in mensagem.items():
                print(i['id'], id)
                if str(i['id']) == str(id):
                    # Atualiza a mensagem para 'Mensagem apagada'
                    print('Atualizando mensagem para "Mensagem apagada"')
                    print(key)
                    print(mensagem[key])
                    mensagem[key] = {
                        'username': i['username'],
                        'message': '<span class="deletedx1"><i class="material-icons block">block</i> <em>Mensagem apagada</em></span>',  # noqa
                        'hora': i['hora'],
                        'dia': i['dia'],
                        'data': i['data'],
                        'id': i['id'],
                        'read': i['read']
                    }
                    print(mensagem[key])
                    # Salva mensagens
                    with open(self.file_path, 'w') as f:
                        print(self.file_path)
                        print('Salvando mensagens')
                        json.dump(self.mensagens, f)
                    return True

        return False

    def user_register(self, user: User):
        ref = db.reference('users')
        ref.push({
            'username': user.user,
            'nickname': user.nickname,
            'password': user.password,
            'last_login': user.today,
            'server_name': user.server_name,
        })
        # print('Usuário registrado')

    def user_login(self, user: User):
        today = datetime.now(tz).strftime('%d/%m/%Y')
        # print(user.nickname, user.password)
        ref = db.reference('users')
        users = ref.order_by_child('nickname').equal_to(user.nickname).get()
        if users:
            for key, value in users.items():
                if value['password'] == user.password:
                    ref.child(key).update({
                        'last_login': today,
                    })
                    # print('Usuário logado')
                    return True
        return False

    def user_id_extract(self, user: User):
        ref = db.reference('users')
        users = ref.order_by_child('nickname').equal_to(user.nickname).get()
        if users:
            for key in users.keys():
                return key

    def user_username_extract(self, user: User):
        ref = db.reference('users')
        users = ref.order_by_child('nickname').equal_to(user.nickname).get()
        if users:
            for value in users.values():
                return value['username']

    def user_exists(self, user: User):
        try:
            ref = db.reference('users')
            users = ref.order_by_child(
                'nickname').equal_to(user.nickname).get()
            if users:
                # print('Usuário existe')
                return True
            # print('Usuário não existe')
            return False
        except Exception:
            return False

    def post_profile_pic_url(self, user: User, foto: str):
        ref = db.reference('users')
        users = ref.order_by_child('nickname').equal_to(user.nickname).get()
        if users:
            for key in users.keys():
                ref.child(key).update({
                    'foto': foto,
                })
                return True
        return False

    def get_profile_pic_url(self, user: Union[User, str]):
        ref = db.reference('users')
        if user is None:
            return False
        try:
            users = ref.order_by_child(
                'nickname').equal_to(user.nickname).get()  # type: ignore
            if users:
                for value in users.values():
                    return False if value['foto'] == 'default.jpg' else True
            return False
        except Exception:
            users = ref.order_by_child('nickname').equal_to(user).get()
            if users:
                for value in users.values():
                    return False if value['foto'] == 'default.jpg' else True
            return False
