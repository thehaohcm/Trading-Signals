
// Real Estate methods
func (r *Repository) GetRealEstatePrices(region, propertyType string) ([]models.RealEstatePrice, error) {
	query := "SELECT id, region, location, price_text, COALESCE(price_numeric, 0), property_type, url, fetched_at FROM real_estate_prices WHERE 1=1"
	args := []interface{}{}
	argCounter := 1

	if region != "" {
		query += fmt.Sprintf(" AND region = $%d", argCounter)
		args = append(args, region)
		argCounter++
	}
	if propertyType != "" {
		query += fmt.Sprintf(" AND property_type = $%d", argCounter)
		args = append(args, propertyType)
		argCounter++
	}

	query += " ORDER BY fetched_at DESC LIMIT 500"

	rows, err := r.DB.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var items []models.RealEstatePrice
	for rows.Next() {
		var i models.RealEstatePrice
		if err := rows.Scan(&i.ID, &i.Region, &i.Location, &i.PriceText, &i.PriceNumeric, &i.PropertyType, &i.URL, &i.FetchedAt); err != nil {
			return nil, err
		}
		items = append(items, i)
	}

	if items == nil {
		items = []models.RealEstatePrice{}
	}

	return items, nil
}
