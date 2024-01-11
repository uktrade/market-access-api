def run(barrier_model, public_barrier_model, dry_run: bool = False):
    public_barriers = public_barrier_model.objects.filter(
        changed_since_published=False
    ).values_list("barrier__id", "last_published_on")

    print(f"Public Barrier Count: {public_barriers.count()}")

    barriers_to_update = []

    for barrier in public_barriers:
        if barrier[1] is not None:
            fields = ["categories_cache", "title", "summary", "country", "sectors", "status"]
            last_history_before_published = barrier_model.history.filter(
                id=barrier[0], history_date__lte=barrier[1]
            ).order_by('-history_date')[:1].values_list(*fields)

            barrier_history = (
                list(barrier_model.history.filter(id=barrier[0], history_date__gt=barrier[1]).values_list(*fields))
                + list(last_history_before_published)
            )

            print(
                f"Public Barrier {barrier[0]} History Count: {len(barrier_history)}"
            )
            changed = False
            for i, historical_record in enumerate(barrier_history):
                if i == len(barrier_history) - 1:
                    break

                if any(
                        [
                            historical_record[0] != barrier_history[i + 1][0],
                            historical_record[1] != barrier_history[i + 1][1],
                            historical_record[2] != barrier_history[i + 1][2],
                            historical_record[3] != barrier_history[i + 1][3],
                            historical_record[4] != barrier_history[i + 1][4],
                            historical_record[5] != barrier_history[i + 1][5],
                        ]
                ):
                    changed = True
                    break

            if changed:
                print(f"Barrier {barrier[0]} changed")
                barriers_to_update.append(barrier[0])

    print('Barriers To Update: ', barriers_to_update)
    if not dry_run and barriers_to_update:
        qs = public_barrier_model.objects.filter(barrier__in=barriers_to_update)
        qs.update(changed_since_published=True)
