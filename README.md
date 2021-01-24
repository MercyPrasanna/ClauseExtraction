# Clause Extraction with Microsoft Azure Services

Many a times it is required to classify documents or extract custom entities of interest from documents. Usually a pre-processing layer is also required to remove headers, footers etc. before a model is called for classification or entity extraction to obtain best results. In-addition, there is also a requirement to have an extraction pipeline to orchestrate the different steps of pre-processing,  model invocation to extract entities, store the extracted entites in a search index or knowledge store. 

The solution described here demonstrate how organizations can use Azure cognitive services to completely automate document classification and clause extraction process.

## Model Development
The solution highlights the usage of Custom Text for building claasification models for document classification and extractor models for entity/clause extraction from documents. Custom Text enables the development of hierachical entities and reuse of one model within another with an approach of machine teaching. Azure Cognitive Search is used to orchestrate the pipeline of calling these models and storing the results in a search index or knowledge store.

![](/media/ModelDevelopmentCustomText.PNG?raw=true)

As Custom Text requires txt documents for training the models, the [preprocessing code](./PreProcessing.AzureFunction.Python) can be used for OCR and also to remove the headers and footers.

## Solution Architecture
Azure Cognitive Search is used for orchestrating the extraction pipeline and storing the extracted results in Azure Cognitive Search Index/Knowledge Store for downstream use.

The Custom Text model for entity extraction and the classification models are integrated to the Azure Cognitive Search pipeline as [Custom Skills](https://docs.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-interface) developed in Python. 

Alternatively, the document classification model can be developed using Automated Machine Learning and integrated using the [Azure Machine Learning Skill](https://docs.microsoft.com/en-us/azure/search/cognitive-search-aml-skill) in Azure Cognitive Search.

![](/media/SolutionArchitecture.PNG?raw=true)

### Process Flow
Azure Cognitive Search Indexer will trigger the AI Pipeline that will,

* Execute a custom skill to crack the document open, OCR and then remove headers and footers. This is an optional skill and only required if custom pre-processing is required. Else the built-in OCR skill would suffice.
* Execute a custom skill that will call the Custom Text entity extraction and classification models.
* Execute a custom skill for post processing to remove duplicate entities.
* The extracted results are stored for exploration in the Azure Cognitive Search Index.

![](/media/CognitiveSearchPipeline.PNG)

Custom Skills were deployed as an Azure Function and Integrated with Azure Cognitive Search.

## Dataset
The dataset was sourced from ['Australian Legal Information Institute'](http://www8.austlii.edu.au/). 

The ['Australian Capital Territory jurisdiction'](http://www8.austlii.edu.au/au/act/) case law PDF documents were used for building the dataset. 

Specifically below tribunal categories were used for the classification models,
* ACT Civil and Administrative Tribunal (ACAT) 2009- (AustLII)
* Discrimination Tribunal of the ACT (ACTDT) 1998-2009 (AustLII)
* Residential Tenancies Tribunal of the ACT (ACTRTT) 1998-2009 (AustLII)
* Tenancy Tribunal of the ACT (ACTTT) 1996-1998 (AustLII)

## Steps
### 1. Develop the Custom Text Entity Extractor and Classification Models

Create the Custom Text application with the extractor and classification models.Provision the Custom Text resource and train the models using the [Custom Text documentation](https://github.com/Azure/luis-document-understanding). This service is currently in private preview and will require whitelisting your subscription.

Sample extractor schema below,

![](/media/Case.PNG?raw=true)

Train the below four classification models to identify the tribunal class.
* discrimination
* civil-administrative
* in-the-tenancy
* residential-tenancies

Below is the snapshot of the models in the Legal Custom Text application,

![](/media/Classes.PNG?raw=true)

Publish the application and score using the prediction end point. 

Sample output from the published application looks like,

```
{
  "prediction": {
    "positiveClassifiers": [
      "discrimination"
    ],
    "classifiers": {
      "discrimination": {
        "score": 0.9729021
      },
      "civil-administrative": {
        "score": 0.05845801
      },
      "in-the-tenancy": {
        "score": 0.0280141551
      },
      "residential-tenancies": {
        "score": 0.0221892167
      }
    },
    "extractors": {
      "case": [
        {
          "jurisdiction": [
            "AUSTRALIAN CAPITAL TERRITORY"
          ]
        },
        {
          "tribunal_category": [
            "DISCRIMINATION TRIBUNAL"
          ]
        },
        {
          "citation": [
            "CITATION: FLETCHER AND RSPCA [2007] ACTDT 5 (19 JUNE 2007)"
          ]
        },
        {
          "catch_words": [
            "Catchwords: Discrimination in provision of goods and services – sexual harassment"
          ]
        },
        {
          "judge": [
            "Mr G C Lalor, Deputy President"
          ]
        },
        {
          "date_of_hearing": [
            "19 June 2007"
          ]
        }
      ]
    }
  }
}
```


### 2. Develop an Azure Cognitive Search Custom Skill for Pre-Processing

Deploy the Python Custom Skill as an Azure Function App using the [Preprocessing code](./ClauseExtraction.AzureFunction.Python).

This custom skill does OCR and also eliminates the header and footers from the documents.

### 3. Develop an Azure Cognitive Search Custom Skill for Clause Extraction and Document Classification

Deploy the Python Custom Skill as an Azure Function App using the [code](/ClauseExtraction.AzureFunction.Python).

#### App Settings to configure
Modify your local.setting.json to point to your LUIS Application, Classifiers and Extractors:

    "luis_location": "YOUR_LUIS_LOCATION",  e.g. westeurope
    "luis_api_key": "YOUR_LUIS_API_KEY",
    "luis_app_id": "YOUR_LUIS_APP_ID",
    "luis_app_slot": "YOUR_LUIS_APP_SLOT", e.g. production
    "luis_classifiers": "YOUR_LUIS_CLASSIFIERS_COMMA_SEPARATED", e.g. classA, classB, classB
    "luis_extractors": "YOUR_LUIS_EXTRACTORS_COMMA_SEPARATED", e.g. entityA, entityB, entityC

Below is the reference documentation that can be helpful for building custom skills in python.

[Functions Bindings Http Webhook Trigger](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger?tabs=python)

[Cognitive Search Defining Skillset](https://docs.microsoft.com/en-us/azure/search/cognitive-search-defining-skillset)

[Cognitive Search Custom Skill Python](https://docs.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-python)

[Visual Studio Code - Deploy Function on Azure](https://docs.microsoft.com/en-us/azure/developer/python/tutorial-vs-code-serverless-python-05)

Sample Input to Clause Extractor Custom Skill:

    {
        "values": [
            {
                "recordId": "1",
                "data": {
                    "text": "AUSTRALIAN CAPITAL TERRITORY RESIDENTIAL TENANCIES TRIBUNAL CITATION: The Commissioner for Social Housing in the ACT v Norman FAULL [2008] ACTRTT (20) RT 758 of 2008 Catchwords: Injury Serious or continuous interference with quiet enjoyment of premises Legislation: Residential Tenancies Act 1997 (ACT) Sections: 51; 104 Tribunal: J Lennard, Member Date: 12 October 2008"
                }
            }
        ]
    }

Sample Output from Clause Extractor Custom Skill:

The skillset outputs the predictions from the classification model as well as the extracted case entity as an complex type. A collection of strings for the predicted classes and a collection of complex type field case is returned. 

    {
        "prediction": {
            "positiveClassifiers": [
                "discrimination"
            ],
            "classifiers": {
                "discrimination": {
                    "score": 0.9729021
                },
                "civil-administrative": {
                    "score": 0.05845801
                },
                "in-the-tenancy": {
                    "score": 0.0280141551
                },
                "residential-tenancies": {
                    "score": 0.0221892167
                }
            },
            "extractors": {
                "case": [{
                    "jurisdiction": [
                        "AUSTRALIAN CAPITAL TERRITORY"
                    ]
                }, {
                    "tribunal_category": [
                        "DISCRIMINATION TRIBUNAL"
                    ]
                }, {
                    "citation": [
                        "CITATION: FLETCHER AND RSPCA [2007] ACTDT 5 (19 JUNE 2007)"
                    ]
                }, {
                    "catch_words": [
                        "Catchwords: Discrimination in provision of goods and services – sexual harassment"
                    ]
                }, {
                    "judge": [
                        "Mr G C Lalor, Deputy President"
                    ]
                }, {
                    "date_of_hearing": [
                        "19 June 2007"
                    ]
                }]
            }
        }
    }

The below definition shows how this custom skill is integrated as part of the Azure Cognitive Search skillset definition.

    {
    "@odata.type": "#Microsoft.Skills.Custom.WebApiSkill",
    "name": "Extract entities from Custom Text Model",
    "description": "Calls an Azure function, which in turn calls Custom Text prediction endpoint",
    "context": "/document",
    "uri": "YOUR_SKILLSET_URI",
    "httpMethod": "POST",
    "timeout": "PT230S",
    "batchSize": 1000,
    "degreeOfParallelism": null,
    "inputs": [
        {
        "name": "text",
        "source": "/document/content"
        }
    ],
    "outputs": [
        {
        "name": "class",
        "targetName": "class"
        },
        {
        "name": "case",
        "targetName": "case"
        }
    ],
    "httpHeaders": null
    }
 
### 4. Postprocessing to remove the Duplicate Entities

Deploy the [strings-distinct](https://github.com/Rodrigossz/Python-Custom-Skills-Toolkit/blob/master/skills/strings-distinct/strings-distinct.md) from the [Python Custom Skill](https://github.com/Rodrigossz/Python-Custom-Skills-Toolkit) repository.

This custom skill helps to eliminate the duplicates in the entities extracted. 

This skill integrates to the Azure Cognitive Search pipeline as shown below. In this example the duplicates in the jurisdiction field of the the case complex type field is eliminated.

    {
        "@odata.type": "#Microsoft.Skills.Custom.WebApiSkill",
        "name": "Jurisdiction Duplicates Removal",
        "description": "EX: To remove duplicates from organizations detected with Entity Extraction processing per page, but saving all of the organizations in /document/organizations.",
        "context": "/document",
        "uri": "YOUR_SKILL_URI",
        "httpMethod": "POST",
        "timeout": "PT30S",
        "batchSize": 1,
        "degreeOfParallelism": null,
        "inputs": [
            {
                "name": "text",
                "source": "/document/case/*/jurisdiction/*"
            }
        ],
        "outputs": [
            {
                "name": "text",
                "targetName": "jurisdiction_unique"
            }
        ],
        "httpHeaders": {}
    }

### 5. Index the documents with an Azure Cognitive Search Pipeline

Deploy the Azure cognitive search pipeline and run the indexer using the resources in [this](/CognitiveSearchResources) folder

a. Replace the below variables in the datasource.json with the storage container details that hosts your documents. 

    YOUR_STORAGE_ACCOUNT_NAME
    YOUR_CONNECTION_STRING
    YOUR_CONTAINER_NAME

b. Replace the below variable in the index.json

    YOUR_INDEX_NAME

c. Replace the below variables with the skillset name and the Azure Function URIs in the skillset.json

    YOUR_SKILLSET_NAME
    YOUR_SKILL_URI

d. Replace the below variables in the indexer.json and run the indexer

    "name" : "YOUR_INDEXER_NAME",
    "dataSourceName" : "YOUR_DATASOURCE_NAME",
    "targetIndexName" : "YOUR_INDEX_NAME",
    "skillsetName" : "YOUR_SKILLSET_NAME",

The indexers output field mapping maps the case entity complex type collection to a collection of primitive type as shown in the sample below. Whereever duplicates are found in entities they go through an additional duplicates removal process.

    {
        "sourceFieldName": "/document/case/*/citation/*",
        "targetFieldName": "citation"
    },
    {
        "sourceFieldName": "/document/case/*/catch_words/*",
        "targetFieldName": "catch_words"
    },
    {
        "sourceFieldName": "/document/tribunal_category_unique/*",
        "targetFieldName": "tribunal_category"
    },
    {
        "sourceFieldName": "/document/date_of_hearing_unique/*",
        "targetFieldName": "date_of_hearing"
    }

### 6. Integrate with UI

The index can be explored either from Azure Cognitive Search portal, postman or integrated with UI using this [UI accelerator](https://github.com/Azure-Samples/azure-search-knowledge-mining). This accelerator can be great starting point if you are new to Azure Cognitive Search.


## Contributors

* Mercy ranjit
* Prakash Lekkala
* Fabrizio Ruocco
