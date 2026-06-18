# Diabetic Foot Ulcer Detection and Mitigation: Harnessing Deep Learning and Agentic AI for Early Intervention

> **MS Thesis** — National University of Computer and Emerging Sciences (FAST), Karachi  
> **Author:** Saif Ul Haq | **Supervisor:** Dr. Muhammad Farrukh Shahid  
> **Department:** Data Science

---

## Overview

This project proposes an end-to-end intelligent pipeline for the detection, severity grading, and clinical management of **Diabetic Foot Ulcers (DFUs)**. The system combines deep learning models with an **Agentic AI** layer powered by **Amazon Bedrock**, enabling autonomous generation of personalized, evidence-based treatment recommendations without requiring clinician intervention at every step.

The pipeline addresses four critical gaps in existing DFU literature: lack of anomaly screening, absence of multi-class severity grading, limited explainability, and no autonomous treatment recommendation.

---

## Dataset Used
https://www.kaggle.com/datasets/laithjj/diabetic-foot-ulcer-dfu

## Pipeline Architecture

The system follows a sequential four-stage workflow:

```
Patient Image → [Stage 1] Anomaly Detection → [Stage 2] Binary Classification
             → [Stage 3] Severity Grading → [Stage 4] Agentic Recommendation
```

### Stage 1 — Anomaly Detection (VAE)
- A **Variational Autoencoder (VAE)** with a VGG-19 encoder filters out out-of-distribution images (non-foot or clinically irrelevant inputs)
- Trained using ELBO loss (MSE reconstruction + KL divergence)
- Reconstruction error threshold: `r = 0.05` (determined on validation set)
- Invalid images are rejected before reaching the classifier

### Stage 2 — Binary Classification (VGG-16)
- Fine-tuned **VGG-16** on ImageNet classifies images as **DFU** or **Normal**
- Last two fully connected layers replaced and retrained
- Trained with data augmentation, dropout, cross-entropy loss, Adam optimizer
- **Best performer** across 8 models tested: **F1 = 92.96% (train), 92.90% (inference)**

### Stage 3 — Severity Grading via Few-Shot Learning (ViT-B/16)
- **5-way 5-shot Prototypical Network** using a **ViT-B/16** backbone
- Grades DFU severity across **5 Wagner classes** (Grade 1–5)
- Classifies by computing Euclidean distance between query embeddings and class prototypes
- Achieved **76.40% accuracy** — best among 9 backbone models tested
- Outperforms Zero-Shot CLIP baseline, especially on visually similar intermediate grades

### Stage 4 — Agentic AI (Amazon Bedrock)
- **Amazon Bedrock Agent** with **Amazon Nova** foundational model
- Queries a structured clinical knowledge base stored in an **S3 Vector Store**
- Generates severity-specific wound management protocols, antibiotic recommendations, referral alerts, and preventive care advice
- Supports **multilingual responses** (including Urdu) for regional accessibility
- Deployed as a full **web application**

---

## Key Results

### Binary Classification Performance

| Model | Acc. (%) | Prec. (%) | Rec. (%) | F1 (%) |
|---|---|---|---|---|
| **VGG-16** | **99.53** | **99.53** | **99.53** | **99.59** |
| VGG-19 | 98.58 | 98.58 | 98.58 | 98.58 |
| AlexNet | 99.05 | 99.04 | 99.04 | 99.04 |
| EfficientNet | 97.63 | 95.58 | 100.00 | 97.74 |
| GoogLeNet | 97.63 | 95.73 | 100.00 | 97.82 |
| ViT-Base | 95.75 | 93.81 | 98.15 | 95.93 |
| ViT-Large | 92.89 | 99.00 | 87.61 | 92.96 |
| CNN (baseline) | 83.41 | 82.01 | 82.90 | 83.25 |

### Few-Shot Severity Grading (5-way 5-shot)

| Model | Accuracy (%) | Rank |
|---|---|---|
| **ViT-B/16** | **76.40** | 1 |
| GoogLeNet | 64.80 | 2 |
| ViT-L/16 | 63.60 | 3 |
| VGG-19 | 60.80 | 4 |
| AlexNet | 42.80 | 9 |

---

## Dataset

- **Binary Classification:** Publicly available Kaggle DFU dataset (2 classes: DFU / Normal)
- **Severity Grading:** Curated dataset spanning all 5 Wagner severity grades; structured as 5-way 5-shot episodes (5 support + 5 query images per class)
- **Split:** 80% train / 20% validation

---

## Tech Stack

| Layer | Tools |
|---|---|
| Deep Learning | PyTorch, torchvision |
| Models | VGG-16/19, AlexNet, EfficientNet, GoogLeNet, ViT-B/16, ViT-L/16, VAE |
| Few-Shot Learning | Prototypical Networks |
| Agentic AI | Amazon Bedrock, Amazon Nova, S3 Vector Store |
| Cloud & Infra | AWS Lambda, AWS S3, AWS IAM, Amazon SageMaker |
| Data & Viz | NumPy, Pandas, OpenCV, scikit-image, Matplotlib, Seaborn |
| Environment | Google Colab + Google Drive |

---

## Ethical Considerations

- Dataset is fully de-identified and used under its Kaggle license for academic purposes only
- Patient images processed in compliance with **GDPR** and **HIPAA** standards
- Encrypted transfers via Amazon S3 API with restricted IAM access
- System outputs are clinical **decision support only** — not a replacement for professional medical judgment

---

## Future Work

- **Multimodal Fusion** — integrating patient metadata (HbA1c, wound history, pain score) with image inputs via cross-attention
- **Larger severity datasets** with active learning to improve few-shot grading beyond 76.40%
- **Continual learning pipeline** to adapt to updated clinical guidelines and regional patient populations

---

## Citation

> Saif Ul Haq, Dr. Muhammad Farrukh Shahid. *"Diabetic Foot Ulcer Detection and Mitigation: Harnessing Deep Learning and Agentic AI for Early Intervention."* MS Thesis, Department of Data Science, FAST-NUCES Karachi, 2025.

---

## Acknowledgements

Supervised by **Dr. Muhammad Farrukh Shahid**, Department of Data Science, FAST-NUCES Karachi.
