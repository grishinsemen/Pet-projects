# Модель данных

## ER-диаграмма

```mermaid
erDiagram
  ENTITY_A ||--o{ ENTITY_B : "связь"
  ENTITY_A {
    int id PK
    string name
  }
  ENTITY_B {
    int id PK
    int entity_a_id FK
    string status
  }
```

## Описание сущностей

### ENTITY_A

| Атрибут | Тип | Обязательный | Описание |
|---|---|---|---|
| id | int | да | Идентификатор |

## Статусы и жизненный цикл

| Статус | Когда наступает | Куда можно перейти |
|---|---|---|
| | | |
