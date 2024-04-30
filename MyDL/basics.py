import os
import MyDL
from MyDL.data import *

def train(model, criterion, optimizer, train_data, val_data, num_epochs=10,
           batch_size=256, lambda_L2=0.001, path='model_params', 
           continue_if_exists=False, calc_val_loss_every_iteration=False):
    model_name = 'MLP3_({},{})_{}_L2-{}_lr-{}'.format(model.hidden_size1, model.hidden_size2, model.activ_func, lambda_L2, optimizer.lr)
    continued_train = False
    if os.path.exists(f'{path}/{model_name}.npz'):
        print(f"Model already exists. Loading model...")
        model.load(f'{path}/{model_name}.npz')
        if not continue_if_exists:
            print(f"Model loaded successfully.")
        else:
            print(f"Model loaded successfully. Training will be continued.")
        continued_train = True
    if continued_train and not continue_if_exists:
        print('Model is not going to be trained further as continue_if_exists is set to False.\n')
        with np.load(os.path.join('results', f'{model_name}.npz')) as results:
            train_loss = results['train_loss'].tolist()
            val_loss = results['val_loss'].tolist()
            train_acc = results['train_acc'].tolist()
            val_acc = results['val_acc'].tolist()
        return train_loss, val_loss, train_acc, val_acc, continued_train
    train_loss_iter, val_loss_iter, train_acc_iter, val_acc_iter = [], [], [], []
    train_loss_epoch, val_loss_epoch, train_acc_epoch, val_acc_epoch = [], [], [], []
    for epoch in range(num_epochs):
        model.train()
        epoch_training_loss = 0.0
        correct = 0
        train_loader = Dataloader(train_data, batch_size, shuffle=True)
        for i, (X_batch, y_batch) in enumerate(train_loader):
            output = model(X_batch)
            loss = criterion(output, y_batch)
            train_loss_iter.append(loss.data)
            L2 = MyDL.MyTensor(0.)
            for param in model.params:
                L2 = L2 + param.square().sum().item()
            loss_with_L2 = loss + lambda_L2 * L2
            epoch_training_loss += loss.data * len(X_batch)
            y_pred = output.data.argmax(axis=1)
            correct += (y_pred == y_batch.data).sum()
            acc = correct / len(train_data)
            train_acc_iter.append(acc)
            optimizer.zero_grad()
            loss_with_L2.backward()
            optimizer.step()
            if calc_val_loss_every_iteration:
                val_loss, val_acc = test(model, val_data, criterion, batch_size)
                val_loss_iter.append(val_loss)
                val_acc_iter.append(val_acc)
        epoch_training_loss /= len(train_data)
        epoch_training_acc = correct / len(train_data)
        train_loss_epoch.append(epoch_training_loss)
        train_acc_epoch.append(epoch_training_acc)
        print(f"Epoch {epoch + 1}/{num_epochs}. Training Loss:   {epoch_training_loss:.3f} \t Accuracy: {epoch_training_acc:.3f}")
        val_loss, val_acc = test(model, val_data, criterion, batch_size)
        val_loss_epoch.append(val_loss)
        val_acc_epoch.append(val_acc)
        spaces = len(f'Epoch {epoch + 1}/{num_epochs}.') * ' '
        print(f"{spaces} Validation Loss: {val_loss:.3f} \t Accuracy: {val_acc:.3f}")
    model.save(filename=f'{model_name}.npz', path=path)
    print('\n')
    return train_loss_epoch, val_loss_epoch, train_acc_epoch, val_acc_epoch, continued_train


def test(model, test_data, criterion, batch_size=256):
    model.eval()
    correct = 0
    loss = 0.0
    test_loader = Dataloader(test_data, batch_size, shuffle=False)
    for X_batch, y_batch in test_loader:
        output = model(X_batch)
        y_pred = output.data.argmax(axis=1)
        correct += (y_pred == y_batch.data).sum()
        loss += criterion(output, y_batch).data * len(X_batch)
    acc = correct / len(test_data)
    loss /= len(test_data)
    model.train()
    return loss, acc


def save_result(train_loss_iter, train_acc_iter, train_loss_epoch, val_loss_epoch, train_acc_epoch, val_acc_epoch, model_name, batch_size, val_loss_iter=None, val_acc_iter=None, continued_train='false', path='results'):
    if not os.path.exists(path):
        os.makedirs(path)
    filename = f'{model_name}.npz'
    path = os.path.join(path, filename)
    train_loss_iter, val_loss_iter, train_acc_iter, val_acc_iter = np.array(train_loss_iter), np.array(val_loss_iter), np.array(train_acc_iter), np.array(val_acc_iter)
    train_loss_epoch, val_loss_epoch, train_acc_epoch, val_acc_epoch = np.array(train_loss_epoch), np.array(val_loss_epoch), np.array(train_acc_epoch), np.array(val_acc_epoch)
    batch_size_arr = np.array([[len(train_loss_iter)], [batch_size]])
    if continued_train:
        prev_results = np.load(path)
        train_loss_iter = np.concatenate((prev_results['train_loss_iter'], train_loss_iter))
        train_acc_iter = np.concatenate((prev_results['train_acc_iter'], train_acc_iter))
        train_loss_epoch = np.concatenate((prev_results['train_loss_epoch'], train_loss_epoch))
        val_loss_epoch = np.concatenate((prev_results['val_loss_epoch'], val_loss_epoch))
        train_acc_epoch = np.concatenate((prev_results['train_acc_epoch'], train_acc_epoch))
        val_acc_epoch = np.concatenate((prev_results['val_acc_epoch'], val_acc_epoch))
        if val_loss_iter is not None:
            val_loss_iter = np.concatenate((prev_results['val_loss_iter'], val_loss_iter))
            val_acc_iter = np.concatenate((prev_results['val_acc_iter'], val_acc_iter))
        till_time = len(train_loss_iter)
        batch_size_arr = np.concatenate((prev_results['batch_size'], [[till_time], [batch_size]]), axis=0)
    np.savez(path, 
             train_loss_iter=train_loss_iter, val_loss_iter=val_loss_iter, train_acc_iter=train_acc_iter, val_acc_iter=val_acc_iter, train_loss_epoch=train_loss_epoch, val_loss_epoch=val_loss_epoch, train_acc_epoch=train_acc_epoch, val_acc_epoch=val_acc_epoch,
             batch_size_till_time = batch_size_arr)


def load_result(model_name, path='results'):
    filename = f'{model_name}.npz'
    path = os.path.join(path, filename)
    with np.load(path) as results:
        train_loss_iter = results['train_loss_iter'].tolist()
        val_loss_iter = results['val_loss_iter'].tolist()
        train_acc_iter = results['train_acc_iter'].tolist()
        val_acc_iter = results['val_acc_iter'].tolist()
        train_loss_epoch = results['train_loss_epoch'].tolist()
        val_loss_epoch = results['val_loss_epoch'].tolist()
        train_acc_epoch = results['train_acc_epoch'].tolist()
        val_acc_epoch = results['val_acc_epoch'].tolist()
        batch_size_till_time = results['batch_size_till_time']
    return {'train_loss_iter': train_loss_iter, 'val_loss_iter': val_loss_iter, 'train_acc_iter': train_acc_iter, 'val_acc_iter': val_acc_iter, 'train_loss_epoch': train_loss_epoch, 'val_loss_epoch': val_loss_epoch, 'train_acc_epoch': train_acc_epoch, 'val_acc_epoch': val_acc_epoch, 'batch_size_till_time': batch_size_till_time}