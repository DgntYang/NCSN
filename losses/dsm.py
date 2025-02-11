import torch
import torch.autograd as autograd


# Denoising score matching
def dsm(energy_net, samples, sigma=1):
    samples.requires_grad_(True)
    vector = torch.randn_like(samples) * sigma
    perturbed_inputs = samples + vector
    logp = -energy_net(perturbed_inputs)
    dlogp = sigma ** 2 * autograd.grad(logp.sum(), perturbed_inputs, create_graph=True)[0]
    kernel = vector
    loss = torch.norm(dlogp + kernel, dim=-1) ** 2
    loss = loss.mean() / 2.

    return loss

# Denoising score estimation
def dsm_score_estimation(scorenet, samples, sigma=0.01):
    perturbed_samples = samples + torch.randn_like(samples) * sigma
    target = - 1 / (sigma ** 2) * (perturbed_samples - samples)
    scores = scorenet(perturbed_samples)
    target = target.view(target.shape[0], -1)
    scores = scores.view(scores.shape[0], -1)
    loss = 1 / 2. * ((scores - target) ** 2).sum(dim=-1).mean(dim=0)

    return loss


# Anneal denoising score estimation
def anneal_dsm_score_estimation(scorenet, samples, labels, sigmas, anneal_power=2.):
    # samples -> X
    # 对应噪声方差/标准差 [128, 1, 1, 1]
    used_sigmas = sigmas[labels].view(samples.shape[0], *([1] * len(samples.shape[1:])))
    # 加入噪声干扰 [128(bs), 1, 28, 28]
    perturbed_samples = samples + torch.randn_like(samples) * used_sigmas
    target = - 1 / (used_sigmas ** 2) * (perturbed_samples - samples)
    # 对加入噪声的数据进行分数预测 [128, 1, 28, 28]
    scores = scorenet(perturbed_samples, labels)
    target = target.view(target.shape[0], -1)  # [128(bs), 784], 下同
    scores = scores.view(scores.shape[0], -1)
    # used_sigmas.squeeze() ** anneal_power 即误差公式中的lambda(sigma_i)
    loss = 1 / 2. * ((scores - target) ** 2).sum(dim=-1) * used_sigmas.squeeze() ** anneal_power

    return loss.mean(dim=0)
