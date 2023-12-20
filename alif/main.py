from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import tbl_mobil_sports as tbl_mobil_sportsModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'cc': 7, 'harga': 4, 'speed': 3, 'berat': 4, 'kapasitas_bensin': 2}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(tbl_mobil_sportsModel.merk_mobil_sports, tbl_mobil_sportsModel.cc, tbl_mobil_sportsModel.harga, tbl_mobil_sportsModel.speed, tbl_mobil_sportsModel.berat, tbl_mobil_sportsModel.kapasitas_bensin)
        result = session.execute(query).fetchall()
        print(result)
        return [{'merk_mobil_sports': tbl_mobil_sports.merk_mobil_sports, 'cc': tbl_mobil_sports.cc, 'harga': tbl_mobil_sports.harga, 'speed': tbl_mobil_sports.speed, 'berat': tbl_mobil_sports.berat, 'kapasitas_bensin': tbl_mobil_sports.kapasitas_bensin} for tbl_mobil_sports in result]

    @property
    def normalized_data(self):
        cc_values = []
        harga_values = []
        speed_values = []
        berat_values = []
        kapasitas_bensin_values = []

        for data in self.data:
            cc_values.append(data['cc'])
            harga_values.append(data['harga'])
            speed_values.append(data['speed'])
            berat_values.append(data['berat'])
            kapasitas_bensin_values.append(data['kapasitas_bensin'])

        return [
            {'merk_mobil_sports': data['merk_mobil_sports'],
             'cc': min(cc_values) / data['cc'],
             'harga': data['harga'] / max(harga_values),
             'speed': data['speed'] / max(speed_values),
             'berat': data['berat'] / max(berat_values),
             'kapasitas_bensin': data['kapasitas_bensin'] / max(kapasitas_bensin_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = []

        for row in normalized_data:
            product_score = (
                row['cc'] ** self.raw_weight['cc'] *
                row['harga'] ** self.raw_weight['harga'] *
                row['speed'] ** self.raw_weight['speed'] *
                row['berat'] ** self.raw_weight['berat'] *
                row['kapasitas_bensin'] ** self.raw_weight['kapasitas_bensin']
            )

            produk.append({
                'merk_mobil_sports': row['merk_mobil_sports'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'merk_mobil_sports': product['merk_mobil_sports'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['merk_mobil_sports']:
                  round(row['cc'] * weight['cc'] +
                        row['harga'] * weight['harga'] +
                        row['speed'] * weight['speed'] +
                        row['berat'] * weight['berat'] +
                        row['kapasitas_bensin'] * weight['kapasitas_bensin'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class tbl_mobil_sports(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(tbl_mobil_sportsModel)
        data = [{'merk_mobil_sports': tbl_mobil_sports.merk_mobil_sports, 'cc': tbl_mobil_sports.cc, 'harga': tbl_mobil_sports.harga, 'speed': tbl_mobil_sports.speed, 'berat': tbl_mobil_sports.berat, 'kapasitas_bensin': tbl_mobil_sports.kapasitas_bensin} for tbl_mobil_sports in session.scalars(query)]
        return self.get_paginated_result('tbl_mobil_sports/', data, request.args), HTTPStatus.OK.value


api.add_resource(tbl_mobil_sports, '/tbl_mobil_sports')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)