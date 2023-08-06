import world
import utils
from world import cprint
import torch
import numpy as np
from tensorboardX import SummaryWriter
import time
import Procedure
from os.path import join
# ==============================
utils.set_seed(world.seed)
print(">>SEED:", world.seed)
# ==============================
import register
from register import dataset
import wandb

wandb.init(project="LightGCN_leverage_contrastive", entity="dain5832")
wandb.run.name = '{}_{}_{}_{}'.format(world.dataset, world.config['weight_type'], world.config['norm_type'], world.config['exp'])
wandb.config.update(world.config)


Recmodel = register.MODELS[world.model_name](world.config, dataset)
Recmodel = Recmodel.to(world.device)
loss_name = getattr(utils, world.config['loss_type'])
loss_class = loss_name(Recmodel, world.config)

Neg_k = 1
if world.config['loss_type'] == 'BCELoss':
    Neg_k = 4

weight_file = utils.getFileName()
print(f"load and save to {weight_file}")
if world.LOAD:
    try:
        Recmodel.load_state_dict(torch.load(weight_file,map_location=torch.device('cpu')))
        world.cprint(f"loaded model weights from {weight_file}")
    except FileNotFoundError:
        print(f"{weight_file} not exists, start from beginning")

# init tensorboard
if world.tensorboard:
    w : SummaryWriter = SummaryWriter(
                                    join(world.BOARD_PATH, time.strftime("%m-%d-%Hh%Mm%Ss-") + "-" + world.comment)
                                    )
else:
    w = None
    world.cprint("not enable tensorflowboard")

try:
    for epoch in range(world.TRAIN_epochs):
        start = time.time()
        if epoch %10 == 0:
            cprint("[TEST]")
            Procedure.Test(dataset, Recmodel, epoch, w, world.config['multicore'], use_orig=False)

        output_information = Procedure.train_original(dataset, Recmodel, loss_class, epoch, neg_k=Neg_k,w=w)
        print(f'EPOCH[{epoch+1}/{world.TRAIN_epochs}] {output_information}')
        torch.save(Recmodel.state_dict(), weight_file)
    cprint("[FINAL TEST]")
    Procedure.Test(dataset, Recmodel, epoch, w, world.config['multicore'], use_orig=False, is_test=True)

finally:
    if world.tensorboard:
        w.close()