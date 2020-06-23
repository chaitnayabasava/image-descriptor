import numpy as np
import math, os, sys
import torch
import torch.nn as nn
import torch.utils.data as data


def train(encoder, decoder, data_loader, vocab_size, args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    encoder.to(device)
    decoder.to(device)

    params = list(decoder.parameters()) + list(encoder.embed.parameters())

    criterion = (
        nn.CrossEntropyLoss().cuda()
        if torch.cuda.is_available()
        else nn.CrossEntropyLoss()
    )
    optimizer = torch.optim.Adam(params=params, lr=0.001)

    total_step = math.ceil(
        len(data_loader.dataset.caption_lengths) / data_loader.batch_sampler.batch_size
    )

    print("----- TRAINING STARTED -----")
    for epoch in range(1, args.epochs + 1):
        for step in range(1, total_step + 1):
            indices = data_loader.dataset.get_indices()
            new_sampler = data.sampler.SubsetRandomSampler(indices=indices)
            data_loader.batch_sampler.sampler = new_sampler

            images, captions = next(iter(data_loader))
            images = images.to(device)
            captions = captions.to(device)

            features = encoder(images)
            outputs = decoder(features, captions)

            loss = criterion(outputs.view(-1, vocab_size), captions.view(-1))

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            stats = "Epoch [%d/%d], Step [%d/%d], Loss: %.4f, Perplexity: %5.4f" % (
                epoch,
                args.epochs,
                step,
                total_step,
                loss.item(),
                np.exp(loss.item()),
            )

            print("\r" + stats, end="")
            sys.stdout.flush()

            if step % args.print_every == 0:
                print("\r" + stats)

        if epoch % args.save_every == 0:
            torch.save(
                {
                    "encoder": encoder.state_dict(),
                    "decoder": decoder.state_dict(),
                    "optimizer": optimizer.state_dict(),
                    "epoch": epoch,
                    "train_step": step,
                },
                os.path.join(
                    args.model_dir, "model-{}-{}.pkl".format(args.model, epoch)
                ),
            )
