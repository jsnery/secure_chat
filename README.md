# SECURE CHAT (WEBAPP FLASK)

O Secure Chat é uma aplicação web de bate-papo seguro desenvolvida com Flask, um framework leve de Python para desenvolvimento web. O projeto utiliza o Firebase como banco de dados em tempo real para armazenar as mensagens e gerenciar a comunicação entre os usuários.

Este projeto foi criado como parte do meu aprendizado do Flask e para praticar conceitos como autenticação de usuário, comunicação em tempo real e integração com serviços de terceiros.

## Como configurar

1. **Crie seu Realtime Database [Firebase](https://firebase.google.com/)**:

Primeiro, você precisa criar um banco de dados Realtime no Firebase. Isso pode ser feito acessando o console do Firebase e seguindo as instruções para criar um novo projeto e um banco de dados Realtime.

2. **Gere sua SDK Firebase**:
Após criar o banco de dados, você precisará gerar as credenciais da sua conta Firebase. Isso inclui a criação de um arquivo JSON que contém informações de autenticação.

3. **Substitua o conteúdo do JSON**:
Substitua o conteúdo do arquivo JSON fornecido (auth.json) com as informações da sua conta Firebase. Este arquivo geralmente contém informações como tipo de projeto, ID do projeto, chave privada, e-mail do cliente, etc.
```json
{
  "type": "",
  "project_id": "",
  "private_key_id": "",
  "private_key": "",
  "client_email": "",
  "client_id": "",
  "auth_uri": "",
  "token_uri": "",
  "auth_provider_x509_cert_url": "",
  "client_x509_cert_url": "",
  "universe_domain": ""
}
```   
4. **Cole o link do seu banco de dados**:
No arquivo ```app/models/json_base.py```, na linha 27, cole o link do seu banco de dados Realtime Firebase. Isso permitirá que o aplicativo Flask se conecte ao seu banco de dados Firebase.
```python
firebase_init(
    'auth.json',
    'https://seudb-rtdb.firebaseio.com/'
)
```

## Execução

1. Clone este repositório:

    ```bash
    git clone https://github.com/jsnery/secure_chat.git
    ```

2. Instale as dependências:

    ```bash
    pip install -r requirements.txt
    ```

3. Após configurar execute o servidor Flask:

    ```bash
    python run.py
    ```

4. Acesse o aplicativo em um navegador da web:

    ```
    http://localhost:5000
    ```
## Funcionalidades

- **Sistema de conversa por ID privado:**
  O aplicativo permite que os usuários se comuniquem de forma privada através de um sistema de mensagens por ID.

- **Sistema de adição de amizade:**
  Os usuários podem adicionar outros usuários como amigos dentro do aplicativo.

- **Armazenamento automático de salas privadas:**
  O aplicativo automaticamente armazena salas de conversa privadas entre usuários.

- **Monitoramento de conversa com amigos em tempo real:**
  O aplicativo monitora as conversas em tempo real entre amigos, permitindo uma experiência de bate-papo em tempo real.

## Notas

- Este projeto é uma versão inicial e pode precisar de mais desenvolvimento e ajustes para atender às suas necessidades específicas.
- Certifique-se de testar o aplicativo completamente e considerar a segurança e o desempenho ao implantá-lo em um ambiente de produção.

[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/richardneri/)

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/jsnery)
