# https://docs.docker.com/language/php/develop/
FROM php:8.2-apache
COPY ./src /var/www/html
COPY custom.conf /etc/apache2/conf-enabled/
RUN a2enmod rewrite
USER www-data
