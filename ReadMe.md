# Python API de gerenciamento de clientes e seus produtos favoritos
Uma implementação em Python de uma API para gerenciamento de clientes e de suas respectivas listas de produtos favoritos, utilizando uma API externa para os dados dos produtos e banco de dados em PostgreSQL.
#### Autor: Leonardo Pahim

## Estrutura da API e seu funcionamento
Cada cliente possui nome, e-mail (único) e uma lista de produtos favoritos. Os produtos utilizados vem da API externa FakeStoreAPI.com, e são referenciados pelo projeto por seu id numérico. (Vale ressaltar que a FakeStoreAPI possui somente 20 produtos).

O administrador deve gerar um token de acesso através do endpoint */api/v1/auth/master-token*, com seu username e senha. As demais rotas são acessadas através desse token JWT como autenticação.

Por ser um projeto demonstrativo, o endpoint de gerar token se encontra na mesma rota junto das demais e o seu login é:
```
{
"username": "favorite_products_admin",
"password": "favorite_products_password"
}
```
**A autenticação está implementada e a senha é comparada com o seu hash, a senha em si não está hardcoded no código.**
**Pelo mesmo motivo de ser um projeto demonstrativo, o arquivo .env está presente no repositório para facilitar o uso da API.**

Ao obter seu token na response do endpoint, o admin pode acessar a janela de autenticação do SwaggerUI e se autenticar com o token JWT, liberando acesso aos demais endpoints de gerenciamento.

As rotas relacionadas ao clientes permitem adicionar, atualizar, deletar e obter as informações de um ou de todos clients cadastrados. (A rota de retornar todos os clientes não retorna a lista de favoritos de todos cadastrados por não ser boas práticas.)

As rotas relacionadas aos produtos favoritos permitem adicionar um produto na lista de favoritos de um cliente, deletar um produto da lista e obter a lista de produtos favoritos de um cliente, a partir de seu UUID.

O projeto possui 4 tabelas, que devem ser geradas pela migração do *alembic* antes da execução do projeto.

A tabela *clients* armazena o nome e email dos clientes e indexada por seu UUID.

A tabela *products_ref* serve como uma tabela de referência armazenando o ID númerico de produtos que fazem parte de pelo menos uma lista de favoritos. Assim é possível evitar dados duplicados, ao contrário seria armazenado toda a informação do produto várias vezes para cada cliente que o favoritou. Quando necessário os dados, para listar os favoritos por exemplo, é realizada uma chamada para a FakeStoreAPI pedindo pelo produto referente ao ID. Foi implementado um cache para que essa chamada não fosse realizada fora das vezes necessárias.

A tabela *client_favorite_products* é essencialmente a lista de produtos favoritos dos clientes, ligando o UUID do cliente com o ID numérico do produto.

A tabela *alembic_version* é criada e utilizada pelo pacote de migrações.

## Escolhas de performance e escalabilidade

### Otimização da indexação no banco de dados
A estrutura das tabelas foi pensada otimizando a busca de dados:
- Todas tabelas são indexadas pelo seu UUID ou ID numéricos, respectivamente.
- A tabela *client_favorite_products* tem o UUID do cliente como FK (chave estrangeira) da tabela de *clients* e seu campo de UUID. Ambas são PK (chaves primárias) beneficiando-se de performance em buscas e validação dos dados. O mesmo acontece na relação com a tabela de *products_ref*.
- O index na coluna de emails de *clients* permite uma validação mais rápida quando lidando com emails repetidos. O mesmo é válido pelo index presente na coluna de nomes.

### Implementação de um cache

Foi implementado um cache para reduzir a quantidade de chamadas externas para a FakeStoreAPI, aumentando a performance. Os dados são tidos como válidos e armazenados por 1 hora, e são utilizados pela função de listar os produtos. Caso não tenha a informação do produto no cache, uma chamada é realizada.

### Processamento assíncrono

FastAPI permite que os requests sejam assíncronos e não bloqueie o processamento de outros requests durante o processamento de um deles.
O SQLAlchemy e o AsyncPG realizam essa mesma função em relação à chamadas no nível de banco de dados.

## Requisitos
- Python 3.8 ou mais novo
- PostgreSQL

## Como rodar o projeto
- Clone o repositório
- Crie e ative um ambiente Python:
  
Supondo Windows no CMD:
```
python -m venv venv
venv\Scripts\activate
```
 
- Instale o arquivo de depêndencias:

```
pip install -r requirements.txt
```

- Através do shell do PostgreSQL, o psql:

Crie o usuário da API no servidor PostgreSQLpsql:

```
CREATE ROLE favorite_products_admin WITH LOGIN PASSWORD 'favorite_products_password';
```

Crie o banco de dados com o dano sendo o usuário da API:

```
CREATE DATABASE fav_prd_db OWNER favorite_products_admin ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8' TEMPLATE = template0;
```

- Por terminal, dentro do projeto:

Crie a migração inicial para criar as tabelas no banco de dados.

```
alembic revision --autogenerate -m "create_initial_tables"
```

Execute a migração:

```
alembic upgrade head
```

- Após as tabelas terem sido criadas no banco de dados, podemos executar a API pelo terminal:

``` 
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- A SwaggerUI estará disponível em http://127.0.0.1:8000/docs


## Explicação dos pacotes utilizados

`fastapi`
`uvicorn[standard]`
`httpx`

FastAPI é o pacote principal da aplicação, é responsável por lidar a estrutura de rotas, receber os requests, validar as respostas deles e gerar a documentação do OpenAPI/Swagger. Uvicorn é responsável por rodar o FastAPI e possui otimizações para lidar com os requests HTTP. HTTPx é um client HTTP para comunicar com a API externa da FakeStore.

`sqlalchemy[asyncio]`
`asyncpg`
`psycopg2-binary`
`alembic`

SQLAlchemy é um tooklit SQL e ORM que lida com a comunicação com o banco, e Alembic lida com migrações, e nesse caso, criação das tabelas inicias do projeto. Visando a escalabilidade e performance, utilizei o asyncio do SQLAlchemy e o Asyncpg para lidar de maneira assíncrona com os acessos ao banco de dados, impedindo que a API tenha que ficar esperando a resposta do banco de dados, sem poder processar demais requests. Psycopg2-binary é necessária para o Alembic.

`passlib[bcrypt]`
`python-jose[criptography]`

Passlib foi usado para criar o hash da senha do admin e verificar ela no login. Python-JOSE é responsável por criar o JWT e validá-lo.

`cachetools`

Cachetools foi utilizada para criar um cache dos pedidos feitos à API externa da FakeStoreAPI. Ao invés de realizar múltiplas chamadas para pegar dados do mesmo produto, a response da API externa é salva internamente, podendo ser acessada por outros requests feitos à API que precisam do mesmo produto. É um cache do tipo TTLCache (Time To Live Cache), e ele tem um tempo configurável de 1 hora para manter os dados. Após esse período, ele fará o request externo quando for pedido tal produto.

`pydantic-settings`
`email-validator`

Pydantic é responsável por lidar com os schemas e modelos da API. Ela atua junto da FastAPI, validando se todos os campos necessários do request estão preenchidos e são do tipo do esperado, respeitando limites e se são opcionais ou não. Usando os modelos da biblioteca é mais fácil lidar com dados vindos do banco de dados, podendo popular eles a partir de objetos ORM. Ela também lida serializando para JSON as responses da API. Email-Validator é usada para ter o campo de tipo e-mail nos modelos da Pydantic. A biblioteca adicional -settings da Pydantic é utilizada para ler variáveis de ambiente e configurações do arquivo .env.
