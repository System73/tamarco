# Contribution guide
Welcome to the project!! First of all we want to thank you, we would like to have new collaborators and contributions.

This project is governed by the Tamarco [Code of Conduct](https://github.com/system73/tamarco/blob/master/CODE_OF_CONDUCT.md) and we expect that all our members follow them.

## Your first contribution

There are so many ways to help, improve the documentation, write tutorials or examples, improve the docstrings, make 
tests, report bugs, etc.

You can take a look at the tickets with the tag `good first issue`.

## Running tests and linters

All the contributions must have at least unit tests. 

Make sure that the test are in the correct place. We have separated the tests in two categories, the unit tests 
(`test/unit`) and the functional tests (`test/functional`). Inside each folder the test should follow the same structure
than the main package. For example, a unit test of `tamarco/core/microservice.py` should be placed in 
`tests/unit/core/test_microservice.py`.

Functional tests are considered those that do some kind of I/O, such as those that need third party services (AMQP, 
Kafka, Postgres, ...), open servers (http and websocket resource), manage files or wait for an event. The goal is
maintain unit tests that can be passed quickly during development.

Most of the functional tests need docker and docker-compose installed in the system to use some third party services.

Before summit a pull request, please check that all the tests and linters are passing.

```
make test
make linters
```

## Code review process

The project maintainers will leave the feedback.

* You need at least two approvals from core developers.
* The tests and linters should pass in the CI.
* The code must have at least the 80% of coverage.
