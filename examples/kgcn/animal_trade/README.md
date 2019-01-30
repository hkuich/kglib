# KGCN Example - CITES Animal Trade Data

### Quickstart

**Requirements:**

- Python 3.6.3 < version < 3.7 ([tensorflow doesn't yet support Python 3.7](https://github.com/tensorflow/tensorflow/issues/17022))
- kglib installed from pip: `pip install --extra-index-url https://test.pypi.org/simple/ grakn-kglib`
- The source code in order to access the example `git clone https://github.com/graknlabs/kglib.git`
- The `grakn-animaltrade.zip` dataset from the [latest release](https://github.com/graknlabs/kglib/releases/latest). This is a dataset that has been pre-loaded into Grakn v1.5 (so you don't have to run the data import yourself), with two keyspaces: `animaltrade_train` and `animaltrade_test`

**To use:**

- Prepare the data:

  - If you already have an instance of Grakn running, make sure to stop it using `./grakn server stop`
  
  - Download the pre-loaded Grakn distribution from the [latest release](https://github.com/graknlabs/kglib/releases/latest)

  - Unzip the distribution `unzip grakn-animaltrade.zip `, where you store this doesn't matter 

  - cd into the distribution `cd grakn-animaltrade`
  
  - start Grakn `./grakn server start`

  - Confirm that the training keyspace is present and contains data 

    `./grakn console -k animaltrade_train`

    `match $t isa traded-item; limit 1; get;`

    and then `exit`

- Run the `main` function of the example: 

  Navigate to the root of the `kglib` repo: `cd kglib`

  Run the example: `python3 -m examples.kgcn.animal_trade.main`

  This will run the full pipeline: retrieving data, building and training a KGCN classifier

#### Details

The CITES dataset details exchanges of animal-based products between countries. In this example we aim to predict the value of `appendix` for a set of samples. This `appendix` can be thought of as the level of endangerment that a `traded-item` is subject to, where `1` represents the highest level of endangerment, and `3` the lowest.

The [main](../../examples/kgcn/animal_trade/main.py) function will:

- Search Grakn for 30 concepts (with attributes as labels) to use as the training set, 30 for the evaluation set, and 30 for the prediction set using queries such as (limiting the returned stream):

  ```
  match $e(exchanged-item: $traded-item) isa exchange, has appendix $appendix; $appendix 1; get;
  ```

  This searches for an `exchange` between countries that has an `appendix` (endangerment level) of `1`, and finds the `traded-item` that was exchanged

- Save those labelled samples to file

- Delete all `appendix` attributes from both `animaltrade_train` and `animaltrade_test` keyspaces. This is the label we will predict in this example, so it should not be present in Grakn otherwise the network can cheat

- Search Grakn for the k-hop neighbours of the selected examples, and store information about them as arrays, demoted in the code as `raw_arrays`. This data is saved to file so that subsequent steps can be re-run without recomputing these data

- Build the TensorFlow computation graph using `model.KGCN`, including a multi-class classification step and learning procedure defined by `downstream.SupervisedKGCNClassifier`

- Feed the `raw_arrays` to the TensorFlow graph, and perform learning