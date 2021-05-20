import glob
import os
import pandas as pd
import torch
import numpy as np

from util import store_models
from util.data.dataframe_factory import DataFrameFactory
from util.full_class_name import fullname
from util.metrics.baseline_losses import bidirectional_cross_entropy, cross_entropy, binary_cross_entropy
from util.metrics import metrics as m
import util.visualize.plot_metrics as plotm
from util.store_models import extract_model_files_from_dir


def auto_find_tested_models_recursive(path='models/'):
    #only works with specific file structure date/modelfolder/files
    files = []
    for root, dirs, dir_files in os.walk(path):
        fm_temp, ch_temp = [], []
        for file in dir_files:
            if 'labels' in file and file.endswith('.csv'):
                fm_temp.append(os.path.join(root, file))
            elif 'output' in file and file.endswith('.csv'):
                ch_temp.append(os.path.join(root, file))
        if len(fm_temp) > 0 and len(ch_temp) > 0:
            files.append(os.path.split(fm_temp[0])[0])
    return files

def auto_find_tested_models(path='models/'):
    csvs = glob.glob(os.path.join(path, '*/*/*.csv')) #Finds all csv files with above structure
    csv_paths = list(reversed(list(set([os.path.abspath(os.path.split(csv)[0]) for csv in csvs]))))
    return csv_paths

def create_model_plots(model_folders, data_loader_index=0):
    TEST_SET = 0; VAL_SET = 1; TRAIN_SET = 2

    model_thresholds = calculate_best_thresholds(model_folders, data_loader_index=VAL_SET)
    for mi, model_folder in enumerate(model_folders):
        try:
            model_name = '.'.join(os.path.split(model_folder)[1].split('.')[-2:]) #fullname(store_models.load_model_architecture(extract_model_files_from_dir(model_folder)[0][0]))
            binary_labels, classes = m.read_binary_label_csv_from_model_folder(model_folder, data_loader_index=data_loader_index)
            predictions, pred_classes = m.read_output_csv_from_model_folder(model_folder, data_loader_index=data_loader_index)
            binary_predictions = m.convert_pred_to_binary(predictions, model_thresholds[mi])

            n_classes = len(classes)
            tpr, fpr, roc_auc, thresholds = m.ROC(binary_labels, predictions)
            tps, fps, best_thresholds = m.select_best_thresholds(tpr, fpr, thresholds, n_classes)
            normal_class = '426783006'
            normal_class_idx = np.where(classes == normal_class)[0][0]
            plotm.plot_roc_multiclass(tpr, fpr, roc_auc, classes, savepath=model_folder, plot_name=model_name)
            plotm.plot_roc_singleclass(tpr, fpr, roc_auc, class_name=normal_class, class_i=normal_class_idx, savepath=model_folder, plot_name=model_name)
        except FileNotFoundError:
            print("File not found")


def create_metric_plots(model_folder, binary_labels, pred, classes):
    print("creating for:", model_folder)
    model_folder_name = os.path.split(model_folder)[1]
    n_classes = len(classes)
    tpr, fpr, roc_auc, thresholds = m.ROC(binary_labels, pred)
    tps, fps, best_thresholds = m.select_best_thresholds(tpr, fpr, thresholds, n_classes)
    zero_fit = m.zero_fit_score(binary_labels, pred, 'macro')
    print('zero_fit, macro', zero_fit)
    zero_fit = m.zero_fit_score(binary_labels, pred, 'micro')
    print('zero_fit, micro', zero_fit)
    class_fit = m.class_fit_score(binary_labels, pred, 'macro')
    print('class_fit, macro', class_fit)
    class_fit = m.class_fit_score(binary_labels, pred, 'micro')

    print('class_fit, micro', class_fit)
    binary_preds = m.convert_pred_to_binary(pred, best_thresholds)

    df = create_metric_score_dataframe(binary_labels, binary_preds, classes, m.f1_scores)
    print(df)
    df = create_metric_score_dataframe(binary_labels, binary_preds, classes, m.recall_scores)
    print(df)
    df = create_metric_score_dataframe(binary_labels, binary_preds, classes, m.precision_scores)
    print(df)
    df = create_metric_score_dataframe(binary_labels, binary_preds, classes, m.accuracy_scores)
    print(df)
    df = create_metric_score_dataframe(binary_labels, binary_preds, classes, m.balanced_accuracy_scores)
    print(df)
    #print(df.to_latex(index=False, label='', caption='LUL'))

    normal_class = '426783006'
    normal_class_idx = np.where(classes == normal_class)[0][0]
    plotm.plot_roc_multiclass(tpr, fpr, roc_auc, classes, savepath=model_folder, plot_name=model_folder_name)
    plotm.plot_roc_singleclass(tpr, fpr, roc_auc, class_name=normal_class, class_i=normal_class_idx, savepath=model_folder, plot_name=model_folder_name)
    #plotm.plot_precision_recall_multiclass(precision, recall, avg_precision, classes, savepath=model_folder, plot_name=model_folder_name)

def create_metric_score_dataframe(binary_labels, binary_preds, classes, metric_function, model_name=None, average_only=False):
    if not average_only:
        scores = metric_function(binary_labels, binary_preds, average=None)
        scdf = pd.DataFrame(scores[np.newaxis, :], columns=classes)
    else:
        scdf = pd.DataFrame()
    scdf.insert(0, 'micro', metric_function(binary_labels, binary_preds, average='micro'), allow_duplicates=True)
    scdf.insert(0, 'macro', metric_function(binary_labels, binary_preds, average='macro'), allow_duplicates=True)
    scdf['model'] = model_name
    scdf = scdf.set_index('model')
    return scdf

def create_metric_confusion_matrix(model_folder, binary_labels, pred, classes:list):
    print("creating for:", model_folder)
    model_folder_name = os.path.split(model_folder)[1]
    n_classes = len(classes)
    tpr, fpr, roc_auc, thresholds = m.ROC(binary_labels, pred)
    tps, fps, best_thresholds = m.select_best_thresholds(tpr, fpr, thresholds, n_classes)
    test_thresholds = {c:0.5 for c in classes}
    binary_preds = m.convert_pred_to_binary(pred, test_thresholds)
    print(binary_preds)
    print(binary_labels)
    cm = m.confusion_matrix(binary_labels, binary_preds)
    print(cm)
    plotm.plot_confusion_matrix(cm, classes)

def create_latex_table(dataframe:pd.DataFrame, output_folder, latex_label='', caption='', filename='table.tex'):
    latex_string = dataframe.to_latex(index=False, label=latex_label, caption=caption)
    with open(os.path.join(output_folder, filename), 'w') as f:
        f.write(latex_string)


def calculate_best_thresholds(model_folders, data_loader_index = 1): #0 = test, 1 = val, 2 = train
    model_thresholds = []
    for mi, model_folder in enumerate(model_folders):
        best_thresholds = None
        try:
            binary_labels, classes = m.read_binary_label_csv_from_model_folder(model_folder, data_loader_index=data_loader_index)
            predictions, pred_classes = m.read_output_csv_from_model_folder(model_folder, data_loader_index=data_loader_index)
            tprs, fprs, roc_auc, thresholds = m.ROC(binary_labels, predictions)
            tpr, fpr, best_thresholds = m.select_best_thresholds(tprs, fprs, thresholds, len(classes))
        except FileNotFoundError as e: #folder with not the correct csv?
            print(e)
        model_thresholds.append(best_thresholds)
    return model_thresholds

def create_paper_metrics(model_folders, data_loader_index=0):
    TEST_SET = 0; VAL_SET = 1; TRAIN_SET = 2

    model_thresholds = calculate_best_thresholds(model_folders, data_loader_index=VAL_SET)

    f1_dff = DataFrameFactory()
    prec_dff = DataFrameFactory()
    rec_dff = DataFrameFactory()
    classfit_dff = DataFrameFactory()
    zerofit_dff = DataFrameFactory()

    for mi, model_folder in enumerate(model_folders):
        try:
            model_name = '.'.join(os.path.split(model_folder)[1].split('.')[-2:]) #fullname(store_models.load_model_architecture(extract_model_files_from_dir(model_folder)[0][0]))
            print(model_name)
            binary_labels, classes = m.read_binary_label_csv_from_model_folder(model_folder, data_loader_index=data_loader_index)
            predictions, pred_classes = m.read_output_csv_from_model_folder(model_folder, data_loader_index=data_loader_index)
            binary_predictions = m.convert_pred_to_binary(predictions, model_thresholds[mi])
            #scores with binary
            f1_dff.append(create_metric_score_dataframe(binary_labels, binary_predictions, classes, m.f1_scores, model_name))
            prec_dff.append(create_metric_score_dataframe(binary_labels, binary_predictions, classes, m.precision_scores, model_name))
            rec_dff.append(create_metric_score_dataframe(binary_labels, binary_predictions, classes, m.recall_scores, model_name))
            #scores with probability
            classfit_dff.append(create_metric_score_dataframe(binary_labels, predictions, classes, m.class_fit_score, model_name))
            zerofit_dff.append(create_metric_score_dataframe(binary_labels, predictions, classes, m.zero_fit_score, model_name))

        except FileNotFoundError as e: #folder with not the correct csv?
            print(e)
    if len(model_folders) > 0:
        ps = list(set([os.path.split(mf)[0] for mf in model_folders])) # GEt all basepaths
        """
        If if models from multiple test sessions are run, put a csv into every of their basepath folders.
        """
        for p in ps:
            print(f"Saving metrics to: {p}")
            #f1_dff.to_csv(p, f'f1-score-dataloader{data_loader_index}.csv')
            #prec_dff.to_csv(p, f'precision-score-dataloader{data_loader_index}.csv')
            #rec_dff.to_csv(p, f'recall-score-dataloader{data_loader_index}.csv')
            f1_dff.to_latex(p, f'f1-score-dataloader{data_loader_index}.tex', caption='F1 Scores', label='tbl:f1scores')
            prec_dff.to_latex(p, f'precision-score-dataloader{data_loader_index}.tex', caption='Precision Scores', label='tbl:precisionscores')
            rec_dff.to_latex(p, f'recall-score-dataloader{data_loader_index}.tex', caption='Precision Scores', label='tbl:recallscores')
            #cst_acc_dff.to_csv(p, f'Custom Accuracy{data_loader_index}.tex')
            classfit_dff.to_latex(p, f'Custom Accuracy (Class Fit){data_loader_index}.tex', caption='Class Fit Scores', label='tbl:classfitscores')
            zerofit_dff.to_latex(p, f'Custom Accuracy (Zero Fit){data_loader_index}.tex', caption='Zero Fit Scores', label='tbl:zerofitscores')
    return model_thresholds



if __name__ == '__main__':
    model_folders = auto_find_tested_models_recursive('models/20_05_21-16-test') #auto_find_tested_models() #or manual list
    TEST_SET = 0; VAL_SET = 1; TRAIN_SET = 2
    create_paper_metrics(model_folders, data_loader_index=TEST_SET) #On Testset
    create_model_plots(model_folders, data_loader_index=TEST_SET)
