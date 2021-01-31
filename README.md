## Flipkart auto buy bot

1. Install docker https://www.docker.com/products/docker-desktop
2. Place it in desktop
3. Change config.env and run the commands below in command prompt
4. cd desktop
5. cd flipbot
6. docker build --rm --tag flipkartbot .
7. docker run -it --rm --env-file=config.env flipkartbot
8. When stock arrives ACCEPT PAYMENT will be displayed and there will be a UPI request

## Video Demo

![](https://github.com/MasterJain/ps5-flipbot/blob/main/botdemo.gif?raw=true)

## Bot will stop after buying one item. Although you can easily modify the code to get more, please dont scalp.
