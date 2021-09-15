require(data.table)
require(ggplot2)

seeds<-fread('/home/anne/Documents/data/seeds/seeds_dataset.txt')
seeds<-seeds[,1:7]

su<-apply(seeds, 2, function(x) mean(x))
va<-apply(seeds, 2, function(x) var(x))


seeds_red<-sapply(1:length(su),function(x) rnorm(210, su[x], va[x]) )
seeds_red<-data.table(cbind(seeds_red))
seeds<-cbind(seeds, seeds_red)
colnames(seeds)<-sapply(1:ncol(seeds), function(x) paste0('V', x))


pca2<-prcomp(seeds)
ggplot(data.table(pca2$x), aes(PC1, PC2))+geom_point()

seeds$name<-sapply(1:nrow(seeds), function(x) paste0('S', x))
seeds<-seeds[, c('name', paste0('V', 1:14))]

fwrite(seeds, "/home/anne/Documents/featurecloud/apps/fc-federated-pca/app/test/test_data/test_data_full.tsv", sep = '\t')
