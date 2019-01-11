exports_files(["requirements.txt"])

load("@io_bazel_rules_python//python:python.bzl", "py_library", "py_test")
load("@pypi_dependencies//:requirements.bzl", "requirement")


load("@graknlabs_rules_deployment//pip:rules.bzl", "deploy_pip")

deploy_pip(
    name = "deploy-pip",
    package_name = "kgcn",
    version_file = "//:VERSION",
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",  # TODO Update
    ],
    url = "https://github.com/graknlabs/kglib",
    author = "Grakn Labs",
    author_email = "community@grakn.ai",
    license = "Apache-2.0",
    install_requires=['astor==0.7.1', 'decorator==4.3.0', 'gast==0.2.0', 'grakn==1.4.2',
                      'grpcio==1.15.0', 'h5py==2.8.0', 'Keras-Applications==1.0.6', 'Keras-Preprocessing==1.0.5',
                      'Markdown==3.0.1', 'networkx==2.2', 'numpy==1.15.2', 'protobuf==3.6.1', 'scikit-learn==0.20.1',
                      'scipy==1.1.0', 'six==1.11.0', 'tensorboard==1.11.0', 'tensorflow==1.11.0',
                      'tensorflow-hub==0.1.1', 'termcolor==1.1.0', 'Werkzeug==0.14.1',
                      'grpcio==1.16.0', 'protobuf==3.6.1', 'six==1.11.0', 'enum34==1.1.6'],
    keywords = ["grakn", "database", "graph", "knowledgebase", "knowledge-engineering"],  # TODO Update
    deployment_properties = "//:deployment.properties",
    description = "A Machine Learning Library for the Grakn knowledge graph.",
    long_description_file = "//:README.md",
    target = ":kgcn"  # TODO
)

py_test(
  name = "my_test",
  srcs = [
      "kgcn/my_test.py"
  ],
  deps = [
      requirement('tensorflow')
  ]
)

py_test(
    name = "ordered_test",
    srcs = [
        "kgcn/neighbourhood/data/sampling/ordered_test.py"
    ],
    deps = [
        "kgcn"
    ],
)

py_test(
    name = "random_sampling_test",
    srcs = [
        "kgcn/neighbourhood/data/sampling/random_sampling_test.py"
    ],
    deps = [
        "kgcn",
    ]
)

#py_test(
#    name = "label_extraction_test",
#    srcs = [
#        "kgcn/use_cases/attribute_prediction/label_extraction_test.py"
#    ],
#    deps = [
#        "kgcn",
#    ]
#)

py_test(
    name = "metrics_test",
    srcs = [
        "kgcn/models/metrics_test.py"
    ],
    deps = [
        "kgcn",
    ]
)

py_test(
    name = "tf_hub_test",
    srcs = [
        "kgcn/encoder/tf_hub_test.py"
    ],
    deps = [
        "kgcn",
    ]
)

py_test(
    name = "schema_test",
    srcs = [
        "kgcn/encoder/schema_test.py"
    ],
    deps = [
        "kgcn",
    ]
)

#py_test(
#    name = "encode_test",
#    srcs = [
#        "kgcn/encoder/encode_test.py"
#    ],
#    deps = [
#        "kgcn",
#    ]
#)

#py_test(
#    name = "data_traversal_test",
#    main = "traversal_test.py",
#    srcs = [
#        "kgcn/neighbourhood/data/traversal_test.py"
#    ],
#    deps = [
#        "kgcn",
#    ]
#)

#py_test(
#    name = "data_executor_test",
#    main = "executor_test.py",
#    srcs = [
#        "kgcn/neighbourhood/data/executor_test.py"
#    ],
#    deps = [
#        "kgcn",
#    ]
#)

#py_test(
#    name = "schema_traversal_test",
#    main = "traversal_test.py",
#    srcs = [
#        "kgcn/neighbourhood/schema/traversal_test.py"
#    ],
#    deps = [
#        "kgcn",
#    ]
#)

#py_test(
#    name = "raw_array_builder_test",
#    srcs = [
#        "kgcn/preprocess/raw_array_builder_test.py"
#    ],
#    deps = [
#        "kgcn",
#    ]
#)

py_library(
    name = "kgcn",
    srcs = glob(['kgcn/**/*.py']),
    deps = [
        requirement('numpy'),
        requirement('scikit-learn'),
        requirement('scipy'),
        requirement('tensorflow'),
        requirement('tensorflow-hub'),

        requirement("protobuf"),
        requirement("grpcio"),
        requirement("six"),
        requirement("enum34"),

        requirement("twine"),
        requirement("setuptools"),
        requirement("wheel"),
        requirement("requests"),
    ]
)